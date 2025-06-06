from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..schemas import AdapterListResponse
from ..schemas.project_schema import ProjectCreate, ProjectResponse
from ..models.project import Project as ProjectModel
from ..utils.query_adapter import QueryAdapter
from datetime import datetime, timezone
from typing import Optional
from fastapi import Request


# Get all projects with pagination and filtering
def get_pagination_projects(
    request: Optional[Request], db: Session
) -> AdapterListResponse[ProjectResponse]:
    allowed_searchs = ["name", "description", "path"]
    base_query = db.query(ProjectModel)
    adapter = QueryAdapter(
        model=ProjectModel,
        request=request,  # Bisa None
        allowed_search_fields=allowed_searchs,
    )
    query, page, limit, count = adapter.adapt(base_query)
    items = query.all()
    data = [ProjectResponse.model_validate(item) for item in items]
    return AdapterListResponse[ProjectResponse](
        page=page, limit=limit, total=count, data=data
    )


def create_project(db: Session, payload: ProjectCreate) -> ProjectResponse:
    project = ProjectModel(
        name=payload.name,
        description=payload.description,
        log_path=payload.log_path,
        is_alert=payload.is_alert,
        framework_type=payload.framework_type,
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


def update_project(
    db: Session, project_id: int, payload: ProjectCreate
) -> ProjectResponse:
    """
    Update a project with the given payload.

    Args:
        db: Database session
        project_id: ID of the project to update
        payload: Project data to update

    Returns:
        ProjectResponse: The updated project

    Raises:
        ValueError: If project not found or update fails
    """
    # Get existing project
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise ValueError(f"Project with ID {project_id} not found")

    # Convert payload to dict and filter valid columns
    update_data = {
        getattr(ProjectModel, key): value
        for key, value in payload.model_dump(exclude_unset=True).items()
        if hasattr(ProjectModel, key)
    }

    # Add updated_at with proper column reference
    update_data[ProjectModel.updated_at] = datetime.now(tz=timezone.utc)
    try:
        # Perform the update
        db.query(ProjectModel).filter(ProjectModel.id == project_id).update(
            update_data, synchronize_session=False
        )

        db.commit()

        # Refresh and return the updated project
        db.refresh(project)
        return ProjectResponse.model_validate(project)

    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Failed to update project: {str(e)}") from e


def get_project_by_id(db: Session, id: int) -> ProjectResponse | None:
    project = db.query(ProjectModel).filter(ProjectModel.id == id).first()
    if not project:
        return None
    return ProjectResponse.model_validate(project)


def get_all_projects(db: Session) -> list[ProjectResponse]:
    projects = db.query(ProjectModel).all()
    return [ProjectResponse.model_validate(project) for project in projects]


def delete_project(db: Session, id: int) -> bool:
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
    project = db.query(ProjectModel).filter(ProjectModel.id == id).first()

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
def project_exists(db: Session, project_id: int) -> bool:
    """Check if project exists by ID"""
    return (
        db.query(ProjectModel).filter(ProjectModel.id == project_id).first() is not None
    )


def get_projects_by_name(db: Session, name: str) -> list[ProjectResponse]:
    """Get projects by name (case-insensitive search)"""
    projects = db.query(ProjectModel).filter(ProjectModel.name.ilike(f"%{name}%")).all()
    return [ProjectResponse.model_validate(project) for project in projects]


def get_active_projects(db: Session) -> list[ProjectResponse]:
    """Get all projects with alerts enabled"""
    projects = db.query(ProjectModel).filter(ProjectModel.is_alert == 1).all()
    return [ProjectResponse.model_validate(project) for project in projects]
