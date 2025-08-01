from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
from fastapi import Request
from datetime import datetime, timezone
from ..models.alarm import Alarm as AlarmModel, AlarmStatus, AlarmSeverity
from ..models.user import User
from ..schemas.alarm_schema import AlarmResponse, AlarmCreate, AlarmUpdate
from ..schemas import AdapterListResponse
from ..utils.query_adapter import QueryAdapter
from ..utils.timezone_utils import convert_utc_to_user_timezone

def get_user_timezone_for_alarm(db: Session, user_id: Optional[int]) -> str:
    """Get user timezone from database, fallback to UTC"""
    if not user_id:
        return 'UTC'
    
    user = db.query(User).filter(User.id == user_id).first()
    if user and hasattr(user, 'user_timezone'):
        return str(user.user_timezone)
    return 'UTC'

def convert_alarm_times_to_user_timezone(alarm_response: AlarmResponse, user_timezone: str) -> AlarmResponse:
    """Convert alarm timestamp fields to user timezone"""
    if alarm_response.triggered_at:
        alarm_response.triggered_at = convert_utc_to_user_timezone(alarm_response.triggered_at, user_timezone)
    if alarm_response.acknowledged_at:
        alarm_response.acknowledged_at = convert_utc_to_user_timezone(alarm_response.acknowledged_at, user_timezone)
    if alarm_response.resolved_at:
        alarm_response.resolved_at = convert_utc_to_user_timezone(alarm_response.resolved_at, user_timezone)
    if alarm_response.created_at:
        alarm_response.created_at = convert_utc_to_user_timezone(alarm_response.created_at, user_timezone)
    if alarm_response.updated_at:
        alarm_response.updated_at = convert_utc_to_user_timezone(alarm_response.updated_at, user_timezone)
    return alarm_response

def get_pagination_alarms(
    request: Optional[Request], db: Session, user_id: Optional[int] = None
) -> AdapterListResponse[AlarmResponse]:
    """Get paginated alarms with filtering and search"""
    allowed_searchs = ["title", "description", "source", "source_id"]
    base_query = db.query(AlarmModel).order_by(AlarmModel.triggered_at.desc())
    adapter = QueryAdapter(
        model=AlarmModel,
        request=request,
        allowed_search_fields=allowed_searchs,
    )
    query, page, limit, count = adapter.adapt(base_query)
    items = query.all()
    
    # Get user timezone
    user_timezone = get_user_timezone_for_alarm(db, user_id)
    
    # Convert times to user timezone
    data = []
    for item in items:
        alarm_response = AlarmResponse.model_validate(item)
        alarm_response = convert_alarm_times_to_user_timezone(alarm_response, user_timezone)
        data.append(alarm_response)
    
    return AdapterListResponse[AlarmResponse](
        page=page, limit=limit, total=count, data=data
    )

def get_all_alarms(db: Session, user_id: Optional[int] = None) -> List[AlarmResponse]:
    """Get all alarms without pagination"""
    alarms = db.query(AlarmModel).order_by(AlarmModel.triggered_at.desc()).all()
    
    # Get user timezone
    user_timezone = get_user_timezone_for_alarm(db, user_id)
    
    # Convert times to user timezone
    data = []
    for alarm in alarms:
        alarm_response = AlarmResponse.model_validate(alarm)
        alarm_response = convert_alarm_times_to_user_timezone(alarm_response, user_timezone)
        data.append(alarm_response)
    
    return data

def create_alarm(db: Session, payload: AlarmCreate) -> AlarmResponse:
    """Create a new alarm"""
    try:
        alarm = AlarmModel(
            title=payload.title,
            description=payload.description,
            severity=payload.severity.upper(),
            source=payload.source,
            source_id=payload.source_id,
            triggered_at=payload.triggered_at or datetime.now(timezone.utc),
        )
        db.add(alarm)
        db.commit()
        db.refresh(alarm)
        return AlarmResponse.model_validate(alarm)
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Failed to create alarm: {str(e)}") from e

def get_alarm_by_id(db: Session, id: int, user_id: Optional[int] = None) -> Optional[AlarmResponse]:
    """Get alarm by ID"""
    alarm = db.query(AlarmModel).filter(AlarmModel.id == id).first()
    if not alarm:
        return None
    
    # Get user timezone
    user_timezone = get_user_timezone_for_alarm(db, user_id)
    
    # Convert times to user timezone
    alarm_response = AlarmResponse.model_validate(alarm)
    alarm_response = convert_alarm_times_to_user_timezone(alarm_response, user_timezone)
    
    return alarm_response

def update_alarm(db: Session, id: int, payload: AlarmUpdate) -> Optional[AlarmResponse]:
    """Update an alarm"""
    alarm = db.query(AlarmModel).filter(AlarmModel.id == id).first()
    if not alarm:
        return None
    
    try:
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(alarm, field, value)
        db.commit()
        db.refresh(alarm)
        return AlarmResponse.model_validate(alarm)
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Failed to update alarm: {str(e)}") from e

def delete_alarm(db: Session, id: int) -> bool:
    """Delete an alarm"""
    alarm = db.query(AlarmModel).filter(AlarmModel.id == id).first()
    if not alarm:
        return False
    try:
        db.delete(alarm)
        db.commit()
        return True
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Failed to delete alarm: {str(e)}")

def acknowledge_alarm(db: Session, id: int) -> Optional[AlarmResponse]:
    """Acknowledge an alarm"""
    alarm = db.query(AlarmModel).filter(AlarmModel.id == id).first()
    if not alarm:
        return None
    
    try:
        setattr(alarm, 'status', AlarmStatus.ACKNOWLEDGED)
        setattr(alarm, 'acknowledged_at', datetime.now(timezone.utc))
        db.commit()
        db.refresh(alarm)
        return AlarmResponse.model_validate(alarm)
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Failed to acknowledge alarm: {str(e)}") from e

def resolve_alarm(db: Session, id: int) -> Optional[AlarmResponse]:
    """Resolve an alarm"""
    alarm = db.query(AlarmModel).filter(AlarmModel.id == id).first()
    if not alarm:
        return None
    
    try:
        setattr(alarm, 'status', AlarmStatus.RESOLVED)
        setattr(alarm, 'resolved_at', datetime.now(timezone.utc))
        setattr(alarm, 'is_active', False)
        db.commit()
        db.refresh(alarm)
        return AlarmResponse.model_validate(alarm)
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Failed to resolve alarm: {str(e)}") from e

def get_active_alarms(db: Session, user_id: Optional[int] = None) -> List[AlarmResponse]:
    """Get all active alarms"""
    alarms = db.query(AlarmModel).filter(
        AlarmModel.is_active,
        AlarmModel.status == AlarmStatus.ACTIVE
    ).order_by(AlarmModel.severity.desc(), AlarmModel.triggered_at.desc()).all()
    
    # Get user timezone
    user_timezone = get_user_timezone_for_alarm(db, user_id)
    
    # Convert times to user timezone
    data = []
    for alarm in alarms:
        alarm_response = AlarmResponse.model_validate(alarm)
        alarm_response = convert_alarm_times_to_user_timezone(alarm_response, user_timezone)
        data.append(alarm_response)
    
    return data

def get_alarms_by_severity(db: Session, severity: AlarmSeverity) -> List[AlarmResponse]:
    """Get alarms by severity level"""
    alarms = db.query(AlarmModel).filter(
        AlarmModel.severity == severity
    ).order_by(AlarmModel.triggered_at.desc()).all()
    return [AlarmResponse.model_validate(alarm) for alarm in alarms]

def get_alarms_by_source(db: Session, source: str, source_id: Optional[str] = None) -> List[AlarmResponse]:
    """Get alarms by source and optionally source_id"""
    query = db.query(AlarmModel).filter(AlarmModel.source == source)
    if source_id:
        query = query.filter(AlarmModel.source_id == source_id)
    
    alarms = query.order_by(AlarmModel.triggered_at.desc()).all()
    return [AlarmResponse.model_validate(alarm) for alarm in alarms]

def acknowledge_all_alarms(db: Session, alarm_ids: Optional[List[int]] = None) -> int:
    """Acknowledge multiple alarms"""
    try:
        query = db.query(AlarmModel).filter(AlarmModel.status == AlarmStatus.ACTIVE)
        
        # If specific alarm IDs provided, filter by them
        if alarm_ids:
            query = query.filter(AlarmModel.id.in_(alarm_ids))
        
        # Update all matching alarms
        updated_count = query.update({
            'status': AlarmStatus.ACKNOWLEDGED,
            'acknowledged_at': datetime.now(timezone.utc)
        }, synchronize_session=False)
        
        db.commit()
        return updated_count
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Failed to acknowledge alarms: {str(e)}") from e

def resolve_all_alarms(db: Session, alarm_ids: Optional[List[int]] = None) -> int:
    """Resolve multiple alarms"""
    try:
        # Build query for alarms that can be resolved (active or acknowledged)
        query = db.query(AlarmModel).filter(
            AlarmModel.status.in_([AlarmStatus.ACTIVE, AlarmStatus.ACKNOWLEDGED])
        )
        
        # If specific alarm IDs provided, filter by them
        if alarm_ids:
            query = query.filter(AlarmModel.id.in_(alarm_ids))
        
        # Update all matching alarms
        updated_count = query.update({
            'status': AlarmStatus.RESOLVED,
            'resolved_at': datetime.now(timezone.utc),
            'is_active': False
        }, synchronize_session=False)
        
        db.commit()
        return updated_count
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Failed to resolve alarms: {str(e)}") from e

def get_alarm_summary(db: Session) -> dict:
    """Get alarm summary statistics"""
    total_alarms = db.query(AlarmModel).count()
    active_alarms = db.query(AlarmModel).filter(
        AlarmModel.is_active,
        AlarmModel.status == AlarmStatus.ACTIVE
    ).count()
    
    critical_alarms = db.query(AlarmModel).filter(
        AlarmModel.severity == AlarmSeverity.CRITICAL,
        AlarmModel.is_active
    ).count()
    
    high_alarms = db.query(AlarmModel).filter(
        AlarmModel.severity == AlarmSeverity.HIGH,
        AlarmModel.is_active
    ).count()
    
    return {
        "total": total_alarms,
        "active": active_alarms,
        "critical": critical_alarms,
        "high": high_alarms,
        "acknowledged": db.query(AlarmModel).filter(
            AlarmModel.status == AlarmStatus.ACKNOWLEDGED
        ).count(),
        "resolved": db.query(AlarmModel).filter(
            AlarmModel.status == AlarmStatus.RESOLVED
        ).count()
    }