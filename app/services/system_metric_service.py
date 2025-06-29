from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional
from fastapi import Request
from sqlalchemy import extract
from ..models.system_metric import SystemMetric as SystemMetricModel
from ..schemas.system_metric_schema import SystemMetricResponse, SystemMetricCreate
from ..schemas import AdapterListResponse
from ..utils.query_adapter import QueryAdapter
import json
from datetime import datetime, timezone

def get_pagination_system_metrics(
    request: Optional[Request], db: Session
) -> AdapterListResponse[SystemMetricResponse]:
    allowed_searchs = ["timestamp", "cpu_percent", "memory_percent"]
    base_query = db.query(SystemMetricModel).order_by(SystemMetricModel.timestamp_log.desc())
    adapter = QueryAdapter(
        model=SystemMetricModel,
        request=request,
        allowed_search_fields=allowed_searchs,
    )
    query, page, limit, count = adapter.adapt(base_query)
    items = query.all()
    data = [SystemMetricResponse.model_validate(item) for item in items]
    return AdapterListResponse[SystemMetricResponse](
        page=page, limit=limit, total=count, data=data
    )


def create_system_metric(db: Session, payload: SystemMetricCreate) -> SystemMetricResponse:
    try:
        metric = SystemMetricModel(
            timestamp_log=payload.timestamp,
            cpu_percent=payload.cpu_percent,
            memory_percent=payload.memory_percent,
            memory_available=payload.memory_available,
            disk_usage=json.dumps(payload.disk_usage),
        )
        db.add(metric)
        db.commit()
        db.refresh(metric)
        return SystemMetricResponse.model_validate(metric)
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Failed to create system metric: {str(e)}") from e


def get_system_metric_by_id(db: Session, id: int) -> Optional[SystemMetricResponse]:
    metric = db.query(SystemMetricModel).filter(SystemMetricModel.id == id).first()
    if not metric:
        return None
    return SystemMetricResponse.model_validate(metric)


def get_all_system_metrics(db: Session) -> list[SystemMetricResponse]:
    metrics = db.query(SystemMetricModel).all()
    return [SystemMetricResponse.model_validate(metric) for metric in metrics]

def get_system_metrics_current_month(db: Session) -> list[SystemMetricResponse]:
    """Get system metrics for current month only"""
    current_date = datetime.now(timezone.utc)
    current_year = current_date.year
    current_month = current_date.month
    
    metrics = db.query(SystemMetricModel).filter(
        extract('year', SystemMetricModel.timestamp_log) == current_year,
        extract('month', SystemMetricModel.timestamp_log) == current_month
    ).order_by(SystemMetricModel.timestamp_log.asc()).all()
    
    return [SystemMetricResponse.model_validate(metric) for metric in metrics]


def get_system_metrics_by_month(db: Session, year: int, month: int) -> list[SystemMetricResponse]:
    """Get system metrics for specific month and year"""
    metrics = db.query(SystemMetricModel).filter(
        extract('year', SystemMetricModel.timestamp_log) == year,
        extract('month', SystemMetricModel.timestamp_log) == month
    ).order_by(SystemMetricModel.timestamp_log.asc()).all()
    
    return [SystemMetricResponse.model_validate(metric) for metric in metrics]


def get_system_metrics_last_30_days(db: Session) -> list[SystemMetricResponse]:
    """Get system metrics for last 30 days"""
    from datetime import timedelta
    
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    
    metrics = db.query(SystemMetricModel).filter(
        SystemMetricModel.timestamp_log >= thirty_days_ago
    ).order_by(SystemMetricModel.timestamp_log.asc()).all()
    
    return [SystemMetricResponse.model_validate(metric) for metric in metrics]


def get_last_system_metric(db: Session) -> Optional[SystemMetricResponse]:
    metric = db.query(SystemMetricModel).order_by(SystemMetricModel.timestamp_log.desc()).first()
    if not metric:
        return None
    return SystemMetricResponse.model_validate(metric)



def get_dashboard_system_metric(db:Session):
    return {
        "last" : get_last_system_metric(db),
        "history" :get_all_system_metrics(db)
    }
def get_dashboard_system_metric_by_month(db: Session, year: int, month: int):
    """Get dashboard data for specific month"""
    return {
        "last": get_last_system_metric(db),
        "history": get_system_metrics_by_month(db, year, month),
        "month": month,
        "year": year
    }


def get_dashboard_system_metric_last_30_days(db: Session):
    """Get dashboard data for last 30 days"""
    return {
        "last": get_last_system_metric(db),
        "history": get_system_metrics_last_30_days(db)
    }


def get_cpu_memory_history_for_chart(db: Session, days: int = 30) -> dict:
    """Get CPU and Memory history optimized for chart display"""
    from datetime import timedelta
    
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Get metrics with reasonable sampling (e.g., every hour if we have too much data)
    metrics = db.query(SystemMetricModel).filter(
        SystemMetricModel.timestamp_log >= start_date
    ).order_by(SystemMetricModel.timestamp_log.asc()).all()
    
    # If we have too many data points, sample them
    if len(metrics) > 100:  # Limit to 100 points for chart performance
        step = len(metrics) // 100
        metrics = metrics[::step]
    
    chart_data = {
        "timestamps": [],
        "cpu_data": [],
        "memory_data": [],
        "total_points": len(metrics)
    }
    
    for metric in metrics:
        # Format timestamp for chart
        timestamp = metric.timestamp_log
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        chart_data["timestamps"].append(timestamp.strftime('%d/%m %H:%M'))
        
        # Safe conversion with proper attribute access
        cpu_value = getattr(metric, 'cpu_percent', 0) or 0
        memory_value = getattr(metric, 'memory_percent', 0) or 0
        
        chart_data["cpu_data"].append(round(float(cpu_value), 1))
        chart_data["memory_data"].append(round(float(memory_value), 1))
    
    return chart_data

def delete_system_metric(db: Session, id: int) -> bool:
    metric = db.query(SystemMetricModel).filter(SystemMetricModel.id == id).first()
    if not metric:
        return False
    try:
        db.delete(metric)
        db.commit()
        return True
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Failed to delete system metric: {str(e)}")