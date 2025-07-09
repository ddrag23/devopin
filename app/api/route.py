from fastapi import APIRouter,Depends
from ..services.project_service import get_all_projects
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..schemas.monitoring_schema import MonitoringData
from ..services.project_log_service import create_project_logs_batch
from ..schemas.project_log_schema import ProjectLogCreate
from ..services.system_metric_service import create_system_metric, get_system_metrics_last_30_days
from ..schemas.system_metric_schema import SystemMetricCreate
from ..services.service_worker_service import update_worker_from_agent,get_all_workers
from ..schemas.service_worker_schema import ServiceWorkerUpdateAgent
from ..services.threshold_monitor import run_threshold_monitoring, get_threshold_monitoring_status
from ..services.alarm_service import create_alarm
from ..schemas.alarm_schema import AlarmCreate
from datetime import datetime
from ..core.logging_config import get_logger

logger = get_logger("app.api")
router = APIRouter()

@router.post("/api/monitoring-data")
async def store_monitoring(data : MonitoringData,db:Session=Depends(get_db)):
    created_alarms = []
    
    try:
        # 1. Insert logs
        all_log_entries = []
        for log_type in data.logs.keys():
            try:
                # Split dengan limit untuk handle project_id yang mungkin ada underscore
                parts = log_type.split("_", 1)
                if len(parts) != 2:
                    error_msg = f"Invalid log_type format: {log_type}, expected 'framework_projectid'"
                    logger.warning(error_msg)
                    continue
                
                fw_type, project_id_str = parts
                project_id = int(project_id_str)
                
                # Process all logs for this log_type
                logs = data.logs.get(log_type, [])
                for log in logs:
                    log_entry = ProjectLogCreate(
                        log_level=log.level,
                        log_time=log.timestamp,
                        project_id=project_id,
                        message=log.message
                    )
                    all_log_entries.append(log_entry)
                
                
                logger.debug(f"Prepared {len(logs)} logs for {log_type} (project_id: {project_id})")
                
            except (ValueError, TypeError) as e:
                error_msg = f"Error processing log_type '{log_type}': {e}"
                logger.warning(error_msg)
                continue
        
        # Batch insert all logs at once
        inserted_logs = []
        if all_log_entries:
            try:
                inserted_logs = create_project_logs_batch(db, all_log_entries)
            except Exception as e:
                logger.error(f"Failed to batch insert logs: {e}")
                # Don't fail the entire request, continue with other operations
        else:
            logger.info("No valid log entries to insert")
        
        # 2. Insert system metric
        system_metrics_dict = data.system_metrics.model_dump() if hasattr(data.system_metrics, "dict") else dict(data.system_metrics)
        if isinstance(system_metrics_dict["timestamp"], str):
        # convert to datetime jika masih string dan belum ISO
            system_metrics_dict["timestamp"] = datetime.fromisoformat(system_metrics_dict["timestamp"])
        
        # Create system metric
        system_metric = create_system_metric(
            db,
            SystemMetricCreate.model_validate(system_metrics_dict)
        )
        logger.info(f"Created system metric: {system_metric.id}")
        
        # 3. Update service workers
        for sw in data.services:
            update_worker_from_agent(
                db,
                sw.name,  # Pass the worker's ID (int) instead of name (str)
                ServiceWorkerUpdateAgent(
                    name=sw.name,
                    description=sw.name,
                    is_monitoring=True,
                    is_enabled=sw.enabled,
                    status=sw.status)
            )
        
        # 4. THRESHOLD MONITORING - Check thresholds and create alarms
        logger.info("Running threshold monitoring...")
        
        # Run threshold monitoring to check for violations using the same db session
        run_threshold_monitoring()
        
        
        return {
            "status": "ok", 
            "message": "Store Monitoring", 
            "data": data,
            "monitoring_result": {
                "system_metric_id": system_metric.id,
                "alarms_created": len(created_alarms),
                "alarm_details": [
                    {
                        "id": alarm.id,
                        "title": alarm.title,
                        "severity": alarm.severity,
                        "source": alarm.source
                    } for alarm in created_alarms
                ] if created_alarms else []
            }
        }
        
    except Exception as e:
        logger.error(f"Error processing monitoring data: {str(e)}")
        # Still return success for data storage, but log the threshold monitoring error
        return {
            "status": "ok", 
            "message": "Store Monitoring (threshold monitoring failed)", 
            "data": data,
            "monitoring_result": {
                "error": str(e),
                "alarms_created": 0
            }
        }

@router.get("/api/projects")
def get_log_path(db:Session = Depends(get_db)):
    projects = get_all_projects(db)
    return {"message" : "OK", "data" : projects}

@router.get("/api/workers")
def get_workers(db:Session = Depends(get_db)):
    workers = get_all_workers(db)
    return {"message" : "OK", "data" : workers}

@router.post("/api/threshold/check")
async def manual_threshold_check():
    """Manually trigger threshold monitoring check"""
    try:
        logger.info("Manual threshold monitoring triggered")
        created_alarms = run_threshold_monitoring()
        
        return {
            "status": "ok",
            "message": "Threshold monitoring completed",
            "result": {
                "alarms_created": len(created_alarms),
                "alarm_details": [
                    {
                        "id": alarm.id,
                        "title": alarm.title,
                        "severity": alarm.severity,
                        "source": alarm.source,
                        "description": alarm.description
                    } for alarm in created_alarms
                ] if created_alarms else []
            }
        }
    except Exception as e:
        logger.error(f"Manual threshold check failed: {str(e)}")
        return {
            "status": "error",
            "message": f"Threshold monitoring failed: {str(e)}",
            "result": {
                "alarms_created": 0,
                "error": str(e)
            }
        }

@router.get("/api/threshold/status")
async def threshold_monitoring_status():
    """Get threshold monitoring system status"""
    try:
        status = get_threshold_monitoring_status()
        return {
            "status": "ok",
            "message": "Threshold monitoring status",
            "data": status
        }
    except Exception as e:
        logger.error(f"Failed to get threshold status: {str(e)}")
        return {
            "status": "error", 
            "message": f"Failed to get status: {str(e)}",
            "data": {
                "enabled_thresholds": 0,
                "last_check": None,
                "recent_metrics": 0,
                "active_cooldowns": 0,
                "error": str(e)
            }
        }

@router.get("/api/metrics/recent")
async def get_recent_metrics(db: Session = Depends(get_db)):
    """Get recent metrics for debugging threshold monitoring"""
    try:
        metrics = get_system_metrics_last_30_days(db)
        return {
            "status": "ok",
            "message": "Recent metrics retrieved",
            "data": {
                "total_metrics": len(metrics),
                "metrics": [
                    {
                        "id": m.id,
                        "cpu_percent": m.cpu_percent,
                        "memory_percent": m.memory_percent, 
                        "timestamp_log": m.timestamp_log.isoformat() if m.timestamp_log else None
                    } for m in metrics[-10:]  # Last 10 metrics
                ]
            }
        }
    except Exception as e:
        logger.error(f"Failed to get recent metrics: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to get metrics: {str(e)}",
            "data": {
                "total_metrics": 0,
                "metrics": []
            }
        }
