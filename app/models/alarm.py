from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Enum
from datetime import datetime, timezone
from app.core.database import Base
import enum

class AlarmSeverity(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlarmStatus(enum.Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"

class Alarm(Base):
    __tablename__ = "alarms"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    severity = Column(Enum(AlarmSeverity), nullable=False, default=AlarmSeverity.MEDIUM)
    status = Column(Enum(AlarmStatus), nullable=False, default=AlarmStatus.ACTIVE)
    source = Column(String(100), nullable=False)  # e.g., "system", "application", "network"
    source_id = Column(String(100))  # optional reference to source entity
    is_active = Column(Boolean, default=True, nullable=False)
    triggered_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    acknowledged_at = Column(DateTime)
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))