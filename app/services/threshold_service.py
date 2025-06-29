from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
from fastapi import Request
from ..models.threshold import Threshold as ThresholdModel, ThresholdType, ThresholdSeverity
from ..schemas.threshold_schema import ThresholdResponse, ThresholdCreate, ThresholdUpdate, ThresholdToggle
from ..schemas import AdapterListResponse
from ..utils.query_adapter import QueryAdapter

def get_pagination_thresholds(
    request: Optional[Request], db: Session
) -> AdapterListResponse[ThresholdResponse]:
    """Get paginated thresholds with filtering and search"""
    allowed_searchs = ["name", "description", "metric_type", "source_filter"]
    base_query = db.query(ThresholdModel).order_by(ThresholdModel.created_at.desc())
    adapter = QueryAdapter(
        model=ThresholdModel,
        request=request,
        allowed_search_fields=allowed_searchs,
    )
    query, page, limit, count = adapter.adapt(base_query)
    items = query.all()
    data = [ThresholdResponse.model_validate(item) for item in items]
    return AdapterListResponse[ThresholdResponse](
        page=page, limit=limit, total=count, data=data
    )

def get_all_thresholds(db: Session) -> List[ThresholdResponse]:
    """Get all thresholds without pagination"""
    thresholds = db.query(ThresholdModel).order_by(ThresholdModel.name).all()
    return [ThresholdResponse.model_validate(threshold) for threshold in thresholds]

def get_enabled_thresholds(db: Session) -> List[ThresholdResponse]:
    """Get only enabled thresholds for monitoring"""
    thresholds = db.query(ThresholdModel).filter(
        ThresholdModel.is_enabled
    ).order_by(ThresholdModel.severity.desc()).all()
    return [ThresholdResponse.model_validate(threshold) for threshold in thresholds]

def create_threshold(db: Session, payload: ThresholdCreate) -> ThresholdResponse:
    """Create a new threshold"""
    try:
        threshold = ThresholdModel(
            name=payload.name,
            description=payload.description,
            metric_type=payload.metric_type.upper(),
            condition=payload.condition.upper(),
            threshold_value=payload.threshold_value,
            duration_minutes=payload.duration_minutes,
            severity=payload.severity.upper(),
            is_enabled=payload.is_enabled,
            source_filter=payload.source_filter,
            cooldown_minutes=payload.cooldown_minutes,
        )
        db.add(threshold)
        db.commit()
        db.refresh(threshold)
        return ThresholdResponse.model_validate(threshold)
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Failed to create threshold: {str(e)}") from e

def get_threshold_by_id(db: Session, id: int) -> Optional[ThresholdResponse]:
    """Get threshold by ID"""
    threshold = db.query(ThresholdModel).filter(ThresholdModel.id == id).first()
    if not threshold:
        return None
    return ThresholdResponse.model_validate(threshold)

def update_threshold(db: Session, id: int, payload: ThresholdUpdate) -> Optional[ThresholdResponse]:
    """Update a threshold"""
    threshold = db.query(ThresholdModel).filter(ThresholdModel.id == id).first()
    if not threshold:
        return None
    
    try:
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(threshold, field, value.upper() if field in ['metric_type','condition','severity'] else value)
        
        db.commit()
        db.refresh(threshold)
        return ThresholdResponse.model_validate(threshold)
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Failed to update threshold: {str(e)}") from e

def toggle_threshold(db: Session, id: int, payload: ThresholdToggle) -> Optional[ThresholdResponse]:
    """Toggle threshold enabled/disabled status"""
    threshold = db.query(ThresholdModel).filter(ThresholdModel.id == id).first()
    if not threshold:
        return None
    
    try:
        setattr(threshold, 'is_enabled', payload.is_enabled)
        db.commit()
        db.refresh(threshold)
        return ThresholdResponse.model_validate(threshold)
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Failed to toggle threshold: {str(e)}") from e

def delete_threshold(db: Session, id: int) -> bool:
    """Delete a threshold"""
    threshold = db.query(ThresholdModel).filter(ThresholdModel.id == id).first()
    if not threshold:
        return False
    try:
        db.delete(threshold)
        db.commit()
        return True
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Failed to delete threshold: {str(e)}")

def get_thresholds_by_type(db: Session, metric_type: ThresholdType) -> List[ThresholdResponse]:
    """Get thresholds by metric type"""
    thresholds = db.query(ThresholdModel).filter(
        ThresholdModel.metric_type == metric_type,
        ThresholdModel.is_enabled
    ).order_by(ThresholdModel.threshold_value.desc()).all()
    return [ThresholdResponse.model_validate(threshold) for threshold in thresholds]

def get_thresholds_by_severity(db: Session, severity: ThresholdSeverity) -> List[ThresholdResponse]:
    """Get thresholds by severity level"""
    thresholds = db.query(ThresholdModel).filter(
        ThresholdModel.severity == severity,
        ThresholdModel.is_enabled
    ).order_by(ThresholdModel.threshold_value.desc()).all()
    return [ThresholdResponse.model_validate(threshold) for threshold in thresholds]

def get_threshold_summary(db: Session) -> dict:
    """Get threshold summary statistics"""
    total_thresholds = db.query(ThresholdModel).count()
    enabled_thresholds = db.query(ThresholdModel).filter(
        ThresholdModel.is_enabled
    ).count()
    
    cpu_thresholds = db.query(ThresholdModel).filter(
        ThresholdModel.metric_type == ThresholdType.CPU,
        ThresholdModel.is_enabled
    ).count()
    
    memory_thresholds = db.query(ThresholdModel).filter(
        ThresholdModel.metric_type == ThresholdType.MEMORY,
        ThresholdModel.is_enabled
    ).count()
    
    disk_thresholds = db.query(ThresholdModel).filter(
        ThresholdModel.metric_type == ThresholdType.DISK,
        ThresholdModel.is_enabled
    ).count()
    
    critical_thresholds = db.query(ThresholdModel).filter(
        ThresholdModel.severity == ThresholdSeverity.CRITICAL,
        ThresholdModel.is_enabled
    ).count()
    
    return {
        "total": total_thresholds,
        "enabled": enabled_thresholds,
        "disabled": total_thresholds - enabled_thresholds,
        "cpu": cpu_thresholds,
        "memory": memory_thresholds,
        "disk": disk_thresholds,
        "critical": critical_thresholds
    }

def duplicate_threshold(db: Session, id: int, new_name: str) -> Optional[ThresholdResponse]:
    """Duplicate an existing threshold with a new name"""
    original = db.query(ThresholdModel).filter(ThresholdModel.id == id).first()
    if not original:
        return None
    
    try:
        duplicate = ThresholdModel(
            name=new_name,
            description=f"Copy of {original.description}" if getattr(original, 'description', None) else None,
            metric_type=original.metric_type,
            condition=original.condition,
            threshold_value=original.threshold_value,
            duration_minutes=original.duration_minutes,
            severity=original.severity,
            is_enabled=False,  # Start disabled for safety
            source_filter=original.source_filter,
            cooldown_minutes=original.cooldown_minutes,
        )
        db.add(duplicate)
        db.commit()
        db.refresh(duplicate)
        return ThresholdResponse.model_validate(duplicate)
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Failed to duplicate threshold: {str(e)}") from e