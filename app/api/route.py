from fastapi import APIRouter,Depends
from ..services.project_service import get_all_projects
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..schemas.monitoring_schema import MonitoringData
router = APIRouter()

@router.post("/api/monitoring-data")
async def store_monitoring(data : MonitoringData):
    print(data)
    return {"status": "ok", "message": "Store Monitoring","data" : data}

@router.get("/api/projects")
def get_log_path(db:Session = Depends(get_db)):
    projects = get_all_projects(db)
    return {"message" : "OK", "data" : projects}
