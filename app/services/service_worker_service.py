from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..schemas import AdapterListResponse
from ..schemas.service_worker_schema import ServiceWorkerCreate,ServiceWorkerResponse
from ..models.service_worker import ServiceWorker as ServiceWorkerModel
from ..utils.query_adapter import QueryAdapter
from datetime import datetime, timezone
from typing import Optional,Dict
from fastapi import Request


def get_pagination_worker(
    request: Optional[Request], db: Session,query_params: Optional[Dict[str, str]] = None
) -> AdapterListResponse[ServiceWorkerResponse]:
    allowed_searchs = ["name", "description", "path"]
    base_query = db.query(ServiceWorkerModel)
    adapter = QueryAdapter(
        model=ServiceWorkerModel,
        request=request,  # Bisa None
        allowed_search_fields=allowed_searchs,
        query_params=query_params,  # Bisa None
    )
    query, page, limit, count = adapter.adapt(base_query)
    items = query.all()
    data = [ServiceWorkerResponse.model_validate(item) for item in items]
    return AdapterListResponse[ServiceWorkerResponse](
        page=page, limit=limit, total=count, data=data
    )


def create_worker(db: Session, payload: ServiceWorkerCreate) -> ServiceWorkerResponse:
    project = ServiceWorkerModel(
        name=payload.name,
        description=payload.description,
        status=payload.status,
        created_at=datetime.now(tz=timezone.utc),
        updated_at=datetime.now(tz=timezone.utc),
    )
    db.add(project)
    try:
        db.commit()
        db.refresh(project)
        return project
    except IntegrityError:
        db.rollback()
        raise ValueError("Failed create data project")


def update_worker(
    db: Session, project_id: int, payload: ServiceWorkerCreate
) -> ServiceWorkerResponse:
    """
    Update a project with the given payload.

    Args:
        db: Database session
        project_id: ID of the project to update
        payload: Project data to update

    Returns:
        ServiceWorkerResponse: The updated project

    Raises:
        ValueError: If project not found or update fails
    """
    # Get existing project
    project = db.query(ServiceWorkerModel).filter(ServiceWorkerModel.id == project_id).first()
    if not project:
        raise ValueError(f"Project with ID {project_id} not found")

    # Convert payload to dict and filter valid columns
    update_data = {
        getattr(ServiceWorkerModel, key): value
        for key, value in payload.model_dump(exclude_unset=True).items()
        if hasattr(ServiceWorkerModel, key)
    }

    # Add updated_at with proper column reference
    update_data[ServiceWorkerModel.updated_at] = datetime.now(tz=timezone.utc)
    try:
        # Perform the update
        db.query(ServiceWorkerModel).filter(ServiceWorkerModel.id == project_id).update(
            update_data, synchronize_session=False
        )

        db.commit()

        # Refresh and return the updated project
        db.refresh(project)
        return ServiceWorkerResponse.model_validate(project)

    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Failed to update project: {str(e)}") from e


def get_worker_by_id(db: Session, id: int) -> ServiceWorkerResponse | None:
    project = db.query(ServiceWorkerModel).filter(ServiceWorkerModel.id == id).first()
    if not project:
        return None
    return ServiceWorkerResponse.model_validate(project)


def get_all_workers(db: Session) -> list[ServiceWorkerResponse]:
    workers = db.query(ServiceWorkerModel).all()
    return [ServiceWorkerResponse.model_validate(project) for project in workers]


def delete_worker(db: Session, id: int) -> bool:
    """
    Delete project by ID

    Args:
        db: Database session
        id: ID of the project to delete

    Returns:
        bool: True if deleted successfully, False if project not found

    Raises:
        ValueError: If deletion fails due to database constraints
    """
    project = db.query(ServiceWorkerModel).filter(ServiceWorkerModel.id == id).first()

    if not project:
        return False

    try:
        db.delete(project)
        db.commit()
        return True
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Failed to delete project: {str(e)}")


# Additional utility functions
def worker_exists(db: Session, project_id: int) -> bool:
    """Check if project exists by ID"""
    return (
        db.query(ServiceWorkerModel).filter(ServiceWorkerModel.id == project_id).first() is not None
    )


def get_workers_by_name(db: Session, name: str) -> list[ServiceWorkerResponse]:
    """Get workers by name (case-insensitive search)"""
    workers = db.query(ServiceWorkerModel).filter(ServiceWorkerModel.name.ilike(f"%{name}%")).all()
    return [ServiceWorkerResponse.model_validate(project) for project in workers]


def get_active_workers(db: Session) -> list[ServiceWorkerResponse]:
    """Get all workers with alerts enabled"""
    workers = db.query(ServiceWorkerModel).filter(ServiceWorkerModel.is_alert == 1).all()
    return [ServiceWorkerResponse.model_validate(project) for project in workers]
