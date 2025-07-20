from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Enum, Text
from datetime import datetime, timezone
from app.core.database import Base
import enum

class ThresholdType(enum.Enum):
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    SERVICE_WORKER_INACTIVE = "service_worker_inactive"

class ThresholdCondition(enum.Enum):
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    EQUALS = "equals"

class ThresholdSeverity(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Threshold(Base):
    __tablename__ = "thresholds"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    
    # Threshold configuration
    metric_type = Column(Enum(ThresholdType), nullable=False)  # cpu, memory, disk
    condition = Column(Enum(ThresholdCondition), nullable=False, default=ThresholdCondition.GREATER_THAN)
    threshold_value = Column(Float, nullable=False)  # percentage value (e.g., 85.0 for 85%)
    duration_minutes = Column(Integer, nullable=False, default=1)  # how long the condition must persist
    
    # Alarm configuration
    severity = Column(Enum(ThresholdSeverity), nullable=False, default=ThresholdSeverity.MEDIUM)
    is_enabled = Column(Boolean, default=True, nullable=False)
    
    # Additional configuration
    source_filter = Column(String(100))  # optional filter for specific sources
    cooldown_minutes = Column(Integer, default=5)  # prevent spam alarms
    
    # Metadata
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
    def __repr__(self):
        return f"<Threshold(name='{self.name}', metric='{self.metric_type}', condition='{self.condition}', value={self.threshold_value})>"