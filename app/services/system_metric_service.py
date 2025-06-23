from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional
from fastapi import Request

from ..models.system_metric import SystemMetric as SystemMetricModel
from ..schemas.system_metric_schema import SystemMetricResponse, SystemMetricCreate
from ..schemas import AdapterListResponse
from ..utils.query_adapter import QueryAdapter
import json


def get_pagination_system_metrics(
    request: Optional[Request], db: Session
) -> AdapterListResponse[SystemMetricResponse]:
    allowed_searchs = ["timestamp", "cpu_percent", "memory_percent"]
    base_query = db.query(SystemMetricModel)
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

def get_last_system_metric(db:Session) -> Optional[SystemMetricResponse]:
    metric = db.query(SystemMetricModel).order_by(SystemMetricModel.timestamp_log.desc()).first()
    if not metric:
        return None
    return SystemMetricResponse.model_validate(metric)

def get_dashboard_system_metric(db:Session):
    return {
        "last" : get_last_system_metric(db),
        "history" :get_all_system_metrics(db)
    }

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