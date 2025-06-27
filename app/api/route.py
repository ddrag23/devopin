from fastapi import APIRouter,Depends
from ..services.project_service import get_all_projects
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..schemas.monitoring_schema import MonitoringData
from ..services.project_log_service import create_project_log
from ..schemas.project_log_schema import ProjectLogCreate
from ..services.system_metric_service import create_system_metric
from ..schemas.system_metric_schema import SystemMetricCreate
from ..services.service_worker_service import update_worker_from_agent,get_all_workers
from ..schemas.service_worker_schema import ServiceWorkerUpdateAgent

from datetime import datetime
router = APIRouter()

@router.post("/api/monitoring-data")
async def store_monitoring(data : MonitoringData,db:Session=Depends(get_db)):
    # print(data)
    # insert logs
    for log_type in data.logs.keys():
        fw_type,project_id = log_type.split("_")
        for log in data.logs.get(log_type,[]):
            create_project_log(db,ProjectLogCreate(log_level=log.level,log_time=log.timestamp,project_id=int(project_id),message=log.message))
    # insert system metric
    system_metrics_dict = data.system_metrics.model_dump() if hasattr(data.system_metrics, "dict") else dict(data.system_metrics)
    if isinstance(system_metrics_dict["timestamp"], str):
    # convert to datetime jika masih string dan belum ISO
        system_metrics_dict["timestamp"] = datetime.fromisoformat(system_metrics_dict["timestamp"])
    create_system_metric(
        db,
        SystemMetricCreate.model_validate(system_metrics_dict)
    )
    
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
    return {"status": "ok", "message": "Store Monitoring","data" : data}

@router.get("/api/projects")
def get_log_path(db:Session = Depends(get_db)):
    projects = get_all_projects(db)
    return {"message" : "OK", "data" : projects}

@router.get("/api/workers")
def get_workers(db:Session = Depends(get_db)):
    workers = get_all_workers(db)
    return {"message" : "OK", "data" : workers}
