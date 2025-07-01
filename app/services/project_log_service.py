from typing import Optional,Dict
from app.models.project_log import ProjectLog as ProjectLogModel
from app.models.user import User
from sqlalchemy.orm import Session
from app.schemas import AdapterListResponse
from fastapi import Request
from app.schemas.project_log_schema import LogResponse,ProjectLogCreate
from app.utils.query_adapter import QueryAdapter
from app.utils.timezone_utils import convert_utc_to_user_timezone, get_user_timezone_from_session, format_datetime_for_user
from sqlalchemy.exc import IntegrityError

def get_user_timezone(db: Session, user_id: Optional[int]) -> str:
    """Get user timezone from database, fallback to UTC"""
    if not user_id:
        return 'UTC'
    
    user = db.query(User).filter(User.id == user_id).first()
    if user and hasattr(user, 'user_timezone'):
        return str(user.user_timezone)
    return 'UTC'

def get_pagination_log_project(
    request: Optional[Request], db: Session, user_id: Optional[int] = None, query_params: Optional[Dict[str, str]] = None
) -> AdapterListResponse[LogResponse]:
    allowed_searchs = ["log_level", "message"]
    base_query = db.query(ProjectLogModel).order_by(ProjectLogModel.log_time.desc())
    adapter = QueryAdapter(
        model=ProjectLogModel,
        request=request,  # Bisa None
        allowed_search_fields=allowed_searchs,
        query_params=query_params,  # Bisa None
    )
    query, page, limit, count = adapter.adapt(base_query)
    items = query.all()
    
    # Get user timezone
    user_timezone = get_user_timezone(db, user_id)
    
    # Convert times to user timezone
    data = []
    for item in items:
        log_response = LogResponse.model_validate(item)
        # Convert UTC times to user timezone
        if log_response.log_time:
            log_response.log_time = convert_utc_to_user_timezone(log_response.log_time, user_timezone)
        if log_response.created_at:
            log_response.created_at = convert_utc_to_user_timezone(log_response.created_at, user_timezone)
        if log_response.updated_at:
            log_response.updated_at = convert_utc_to_user_timezone(log_response.updated_at, user_timezone)
        data.append(log_response)
    
    return AdapterListResponse[LogResponse](
        page=page, limit=limit, total=count, data=data
    )

def get_project_log_by_id(db: Session, log_id: int, user_id: Optional[int] = None) -> Optional[LogResponse]:
    """Get single project log by ID with timezone conversion"""
    log_item = db.query(ProjectLogModel).filter(ProjectLogModel.id == log_id).first()
    if not log_item:
        return None
    
    # Get user timezone
    user_timezone = get_user_timezone(db, user_id)
    
    # Convert to response model
    log_response = LogResponse.model_validate(log_item)
    
    # Convert UTC times to user timezone
    if log_response.log_time:
        log_response.log_time = convert_utc_to_user_timezone(log_response.log_time, user_timezone)
    if log_response.created_at:
        log_response.created_at = convert_utc_to_user_timezone(log_response.created_at, user_timezone)
    if log_response.updated_at:
        log_response.updated_at = convert_utc_to_user_timezone(log_response.updated_at, user_timezone)
    
    return log_response
    
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
