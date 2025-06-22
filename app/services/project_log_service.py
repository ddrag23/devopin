from typing import Optional,Dict
from app.models.project_log import ProjectLog as ProjectLogModel
from sqlalchemy.orm import Session
from app.schemas import AdapterListResponse
from fastapi import Request
from app.schemas.project_log_schema import LogResponse,ProjectLogCreate
from app.utils.query_adapter import QueryAdapter
from sqlalchemy.exc import IntegrityError

def get_pagination_log_project(
    request: Optional[Request], db: Session,query_params: Optional[Dict[str, str]] = None
) -> AdapterListResponse[LogResponse]:
    allowed_searchs = ["log_level", "message"]
    base_query = db.query(ProjectLogModel)
    adapter = QueryAdapter(
        model=ProjectLogModel,
        request=request,  # Bisa None
        allowed_search_fields=allowed_searchs,
        query_params=query_params,  # Bisa None
    )
    query, page, limit, count = adapter.adapt(base_query)
    items = query.all()
    data = [LogResponse.model_validate(item) for item in items]
    return AdapterListResponse[LogResponse](
        page=page, limit=limit, total=count, data=data
    )
    
def create_project_log(db: Session, payload: ProjectLogCreate) -> LogResponse:
    project = ProjectLogModel(
        log_level=payload.log_level,
        message=payload.message,
        project_id=payload.project_id,
        log_time=payload.log_time
    )
    db.add(project)
    try:
        db.commit()
        db.refresh(project)
        return project
    except IntegrityError:
        db.rollback()
        raise ValueError("Failed create data project")
