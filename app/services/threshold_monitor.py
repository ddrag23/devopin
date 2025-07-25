from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime, timezone, timedelta
from ..models.threshold import Threshold as ThresholdModel, ThresholdType, ThresholdCondition
from ..models.system_metric import SystemMetric as SystemMetricModel
from ..models.alarm import Alarm as AlarmModel
from ..models.service_worker import ServiceWorker as ServiceWorkerModel
from ..services.threshold_service import get_enabled_thresholds
from ..services.alarm_service import create_alarm
from ..schemas.alarm_schema import AlarmCreate
from ..utils.db_context import db_context
import json
from ..core.logging_config import get_logger
from sqlalchemy import func

logger = get_logger("app.threshold_monitor")

class ThresholdMonitor:
    """Service to monitor system metrics against configured thresholds and create alarms"""
    
    def __init__(self):
        self.last_alarm_times: Dict[int, datetime] = {}  # Track last alarm time per threshold
    
    def check_all_thresholds(self, db: Session) -> List[AlarmModel]:
        """Check all enabled thresholds against recent metrics and create alarms if needed"""
        created_alarms = []
        
        try:
            # Get all enabled thresholds
            thresholds = get_enabled_thresholds(db)
            
            if not thresholds:
                logger.info("No enabled thresholds found")
                return created_alarms
            
            logger.info(f"Checking {len(thresholds)} enabled thresholds")
            
            for threshold in thresholds:
                try:
                    alarm = self._check_threshold(db, threshold)
                    if alarm:
                        created_alarms.append(alarm)
                        logger.info(f"Created alarm for threshold: {threshold.name}")
                except Exception as e:
                    logger.error(f"Error checking threshold {threshold.name}: {str(e)}")
                    continue
            
            return created_alarms
            
        except Exception as e:
            logger.error(f"Error in check_all_thresholds: {str(e)}")
            return created_alarms
    
    def _check_threshold(self, db: Session, threshold) -> Optional[AlarmModel]:
        """Check a single threshold against recent metrics or service workers"""
        
        # Check cooldown period to prevent spam alarms
        if not self._is_cooldown_expired(threshold):
            return None
        
        # Handle service worker inactive threshold
        if threshold.metric_type.value.lower() == ThresholdType.SERVICE_WORKER_INACTIVE.value:
            return self._check_service_worker_threshold(db, threshold)
        
        # Handle system metrics thresholds (CPU, memory, disk)
        return self._check_system_metric_threshold(db, threshold)
    
    def _check_system_metric_threshold(self, db: Session, threshold) -> Optional[AlarmModel]:
        """Check threshold against system metrics (CPU, memory, disk)"""
        
        # Get metrics for the duration period
        duration_minutes = threshold.duration_minutes
        start_time = datetime.now(timezone.utc) - timedelta(minutes=duration_minutes)
        
        # Query metrics in the time window
        metrics_query = db.query(SystemMetricModel).filter(
            SystemMetricModel.timestamp_log >= start_time
        ).order_by(SystemMetricModel.timestamp_log.desc())
        
        metrics = metrics_query.all()
        
        if not metrics:
            logger.info(f"No metrics found for threshold {threshold.name}")
            return None
        
        # Check if threshold condition is met for the entire duration
        if self._evaluate_threshold_condition(threshold, metrics):
            # Create alarm
            alarm = self._create_threshold_alarm(db, threshold, metrics[0])  # Use latest metric
            if alarm:
                # Update last alarm time
                self.last_alarm_times[threshold.id] = datetime.now(timezone.utc)
            return alarm
        
        return None
    
    def _check_service_worker_threshold(self, db: Session, threshold) -> Optional[AlarmModel]:
        """Check threshold for service worker inactivity"""
        
        inactive_minutes = threshold.threshold_value  # For service workers, this is the inactivity threshold in minutes
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=inactive_minutes)
        
        # Query for service workers that haven't been updated since cutoff_time
        print(cutoff_time)
        query = db.query(ServiceWorkerModel).filter(
            ServiceWorkerModel.updated_at < cutoff_time,
            ServiceWorkerModel.is_monitoring == 1,
            ServiceWorkerModel.status == 'inactive'  # Only check workers that should be monitored
        )
        
        # Apply source filter if specified (worker name filter)
        if threshold.source_filter:
            # Exact match for service worker name
            query = query.filter(ServiceWorkerModel.name == threshold.source_filter)
        inactive_workers = query.all()
        print(f"Query returned {len(inactive_workers)} workers")
        
        if not inactive_workers:
            logger.info(f"No inactive service workers found for threshold {threshold.name}")
            return None
        
        # Create alarm for the first inactive worker found
        worker = inactive_workers[0]
        
        # Calculate how long the worker has been inactive
        # Ensure worker.updated_at is timezone-aware
        worker_updated_at = worker.updated_at
        if worker_updated_at.tzinfo is None:
            worker_updated_at = worker_updated_at.replace(tzinfo=timezone.utc)
        
        inactive_duration = datetime.now(timezone.utc) - worker_updated_at
        inactive_minutes_actual = int(inactive_duration.total_seconds() / 60)
        
        alarm = self._create_service_worker_alarm(db, threshold, worker, inactive_minutes_actual)
        if alarm:
            # Update last alarm time
            self.last_alarm_times[threshold.id] = datetime.now(timezone.utc)
        
        return alarm
    
    def _is_cooldown_expired(self, threshold) -> bool:
        """Check if cooldown period has expired for this threshold"""
        if threshold.id not in self.last_alarm_times:
            return True
        
        last_alarm_time = self.last_alarm_times[threshold.id]
        cooldown_period = timedelta(minutes=threshold.cooldown_minutes)
        
        return datetime.now(timezone.utc) - last_alarm_time >= cooldown_period
    
    def _evaluate_threshold_condition(self, threshold, metrics: List[SystemMetricModel]) -> bool:
        """Evaluate if threshold condition is met for all metrics in the duration"""
        
        if len(metrics) == 0:
            return False
        
        # We need metrics spanning the entire duration to trigger
        duration_seconds = threshold.duration_minutes * 60
        latest_metric_time = metrics[0].timestamp_log
        earliest_required_time = latest_metric_time - timedelta(seconds=duration_seconds)
        
        # Filter metrics within the required time window
        relevant_metrics = [
            m for m in metrics 
            if getattr(m, 'timestamp_log') >= earliest_required_time
        ]
        if len(relevant_metrics) < 2:  # Need at least 2 points to establish a trend
            return False
        
        # Check if ALL metrics in the window violate the threshold
        violation_count = 0
        total_count = len(relevant_metrics)
        
        for metric in relevant_metrics:
            if self._metric_violates_threshold(threshold, metric):
                violation_count += 1
        
        # Require at least 80% of metrics to violate the threshold
        violation_ratio = violation_count / total_count
        return violation_ratio >= 0.8
    
    def _metric_violates_threshold(self, threshold, metric: SystemMetricModel) -> bool:
        """Check if a single metric violates the threshold condition"""
        
        # Get the metric value based on threshold type
        if threshold.metric_type.value.lower() == ThresholdType.CPU.value:
            metric_value = metric.cpu_percent or 0
        elif threshold.metric_type.value.lower() == ThresholdType.MEMORY.value:
            metric_value = metric.memory_percent or 0
        elif threshold.metric_type.value.lower() == ThresholdType.DISK.value:
            # For disk, we'll check the highest usage percentage across all disks
            try:
                disk_usage_str = getattr(metric, 'disk_usage', '{}') or '{}'
                disk_data = json.loads(disk_usage_str)
                if not disk_data:
                    return False
                
                max_disk_usage = max(
                    disk_info.get('percent', 0) 
                    for disk_info in disk_data.values() 
                    if isinstance(disk_info, dict)
                )
                metric_value = max_disk_usage
            except (json.JSONDecodeError, ValueError, AttributeError):
                return False
        else:
            return False
        
        # Evaluate condition
        threshold_value = threshold.threshold_value
        
        if threshold.condition.value.lower() == ThresholdCondition.GREATER_THAN.value:
            return metric_value > threshold_value
        elif threshold.condition.value.lower() == ThresholdCondition.LESS_THAN.value:
            return metric_value < threshold_value
        elif threshold.condition.value.lower() == ThresholdCondition.EQUALS.value:
            # For equals, we'll use a small tolerance (±1%)
            return abs(metric_value - threshold_value) <= 1.0
        
        return False
    
    def _create_threshold_alarm(self, db: Session, threshold, latest_metric: SystemMetricModel) -> Optional[AlarmModel]:
        """Create an alarm for a threshold violation"""
        
        try:
            # Map threshold severity to alarm severity
            severity_map = {
                'low': 'low',
                'medium': 'medium', 
                'high': 'high',
                'critical': 'critical'
            }
            
            # Get current metric value for context
            if threshold.metric_type.value.lower() == ThresholdType.CPU.value:
                current_value = latest_metric.cpu_percent or 0
                metric_unit = "%"
            elif threshold.metric_type.value.lower() == ThresholdType.MEMORY.value:
                current_value = latest_metric.memory_percent or 0
                metric_unit = "%"
            elif threshold.metric_type.value.lower() == ThresholdType.DISK.value:
                try:
                    disk_usage_str = getattr(latest_metric, 'disk_usage', '{}') or '{}'
                    disk_data = json.loads(disk_usage_str)
                    current_value = max(
                        disk_info.get('percent', 0) 
                        for disk_info in disk_data.values() 
                        if isinstance(disk_info, dict)
                    ) if disk_data else 0
                    metric_unit = "%"
                except (json.JSONDecodeError, ValueError, AttributeError):
                    current_value = 0
                    metric_unit = "%"
            else:
                current_value = 0
                metric_unit = ""
            
            # Create alarm description
            condition_text = {
                'greater_than': 'exceeded',
                'less_than': 'below',
                'equals': 'equals'
            }.get(threshold.condition.value.lower(), 'violated')
            
            description = (
                f"{threshold.metric_type.value.upper()} {condition_text} threshold of {threshold.threshold_value}% "
                f"for {threshold.duration_minutes} minutes. "
                f"Current value: {current_value:.1f}{metric_unit}"
            )
            
            # Create alarm payload
            from ..schemas.alarm_schema import AlarmSeverityEnum
            severity_value = severity_map.get(threshold.severity.value.lower(), 'medium')
            alarm_payload = AlarmCreate(
                title=f"Threshold Alert: {threshold.name}",
                description=description,
                severity=AlarmSeverityEnum(severity_value),
                source="threshold_monitor",
                source_id=str(threshold.id),
                triggered_at=datetime.now(timezone.utc)
            )
            
            # Create the alarm using the alarm service
            alarm_response = create_alarm(db, alarm_payload)
            
            # Return the created alarm model (we need to fetch it again)
            if alarm_response:
                return db.query(AlarmModel).filter(AlarmModel.id == alarm_response.id).first()
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating alarm for threshold {threshold.name}: {str(e)}")
            return None
    
    def _create_service_worker_alarm(self, db: Session, threshold, worker: ServiceWorkerModel, inactive_minutes: int) -> Optional[AlarmModel]:
        """Create an alarm for service worker inactivity"""
        
        try:
            # Map threshold severity to alarm severity
            severity_map = {
                'low': 'low',
                'medium': 'medium', 
                'high': 'high',
                'critical': 'critical'
            }
            
            # Create alarm description
            # Ensure worker.updated_at is timezone-aware for display
            worker_updated_at = worker.updated_at
            if worker_updated_at.tzinfo is None:
                worker_updated_at = worker_updated_at.replace(tzinfo=timezone.utc)
            
            description = (
                f"Service worker '{worker.name}' has been inactive for {inactive_minutes} minutes, "
                f"exceeding the threshold of {threshold.threshold_value} minutes. "
                f"Last activity: {worker_updated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}"
            )
            
            # Create alarm payload
            from ..schemas.alarm_schema import AlarmSeverityEnum
            severity_value = severity_map.get(threshold.severity.value.lower(), 'medium')
            alarm_payload = AlarmCreate(
                title=f"Service Worker Inactive: {worker.name}",
                description=description,
                severity=AlarmSeverityEnum(severity_value),
                source="service_worker_monitor",
                source_id=str(worker.id),
                triggered_at=datetime.now(timezone.utc)
            )
            
            # Create the alarm using the alarm service
            alarm_response = create_alarm(db, alarm_payload)
            
            # Return the created alarm model (we need to fetch it again)
            if alarm_response:
                return db.query(AlarmModel).filter(AlarmModel.id == alarm_response.id).first()
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating service worker alarm for worker {worker.name}: {str(e)}")
            return None

# Global monitor instance
threshold_monitor = ThresholdMonitor()

def run_threshold_monitoring() -> List[AlarmModel]:
    """Run threshold monitoring and return created alarms"""
    try:
        with db_context() as db:
            return threshold_monitor.check_all_thresholds(db)
    except Exception as e:
        logger.error(f"Error in run_threshold_monitoring: {str(e)}")
        return []

def check_threshold_by_id(threshold_id: int) -> Optional[AlarmModel]:
    """Check a specific threshold by ID"""
    try:
        with db_context() as db:
            threshold = db.query(ThresholdModel).filter(
                ThresholdModel.id == threshold_id,
                ThresholdModel.is_enabled
            ).first()
            
            if not threshold:
                return None
            
            from ..schemas.threshold_schema import ThresholdResponse
            threshold_response = ThresholdResponse.model_validate(threshold)
            return threshold_monitor._check_threshold(db, threshold_response)
            
    except Exception as e:
        logger.error(f"Error checking threshold {threshold_id}: {str(e)}")
        return None

def get_threshold_monitoring_status() -> Dict:
    """Get status of threshold monitoring"""
    try:
        with db_context() as db:
            enabled_thresholds = get_enabled_thresholds(db)
            
            # Get recent metrics count
            recent_time = datetime.now(timezone.utc) - timedelta(minutes=5)
            recent_metrics_count = db.query(SystemMetricModel).filter(
                SystemMetricModel.timestamp_log >= recent_time
            ).count()
            
            return {
                "enabled_thresholds": len(enabled_thresholds),
                "last_check": datetime.now(timezone.utc).isoformat(),
                "recent_metrics": recent_metrics_count,
                "active_cooldowns": len(threshold_monitor.last_alarm_times)
            }
            
    except Exception as e:
        logger.error(f"Error getting monitoring status: {str(e)}")
        return {
            "enabled_thresholds": 0,
            "last_check": None,
            "recent_metrics": 0,
            "active_cooldowns": 0,
            "error": str(e)
        }