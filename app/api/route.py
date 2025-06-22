from fastapi import APIRouter,Depends
from ..services.project_service import get_all_projects
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..schemas.monitoring_schema import MonitoringData
from ..services.project_log_service import create_project_log
from ..schemas.project_log_schema import ProjectLogCreate
router = APIRouter()

@router.post("/api/monitoring-data")
async def store_monitoring(data : MonitoringData,db:Session=Depends(get_db)):
    print(data)
    for log in data.logs.get("laravel",[]):
        create_project_log(db,ProjectLogCreate(log_level=log.level,log_time=log.timestamp,project_id=1,message=log.message))
    return {"status": "ok", "message": "Store Monitoring","data" : data}

@router.get("/api/projects")
def get_log_path(db:Session = Depends(get_db)):
    projects = get_all_projects(db)
    return {"message" : "OK", "data" : projects}
