from pydantic import BaseModel
from fastapi import Form
from datetime import datetime,timezone

# User
class ProjectLogBase(BaseModel):
    log_level:str
    message:str
    log_time:datetime

class ProjectLogCreate(ProjectLogBase):
    project_id: int
    @classmethod
    def as_form(
        cls,
        log_level: str = Form(...),
        message: str = Form(...),
        project_id: int = Form(...),
        log_time : datetime = Form(datetime.now(timezone.utc))
    ):
        return cls(log_level=log_level,message=message,project_id=project_id,log_time=log_time)
    

class LogResponse(ProjectLogBase):
    created_at: datetime
    updated_at: datetime
    id:int
    project_id : int
    class Config:
        from_attributes = True
 
