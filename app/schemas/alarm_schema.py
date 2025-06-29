from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional
from enum import Enum

class AlarmSeverityEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlarmStatusEnum(str, Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"

class AlarmBase(BaseModel):
    title: str
    description: Optional[str] = None
    severity: AlarmSeverityEnum = AlarmSeverityEnum.MEDIUM
    source: str
    source_id: Optional[str] = None

class AlarmCreate(AlarmBase):
    triggered_at: Optional[datetime] = None
    
    @field_validator("triggered_at", mode="before")
    @classmethod
    def parse_triggered_at(cls, value: str | datetime | None) -> datetime:
        if value is None:
            return datetime.now()

        if isinstance(value, datetime):
            return value

        try:
            if "T" in value:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid datetime format: {value}") from e

class AlarmUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[AlarmSeverityEnum] = None
    status: Optional[AlarmStatusEnum] = None
    source: Optional[str] = None
    source_id: Optional[str] = None
    is_active: Optional[bool] = None

class AlarmResponse(AlarmBase):
    id: int
    status: AlarmStatusEnum
    is_active: bool
    triggered_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    @field_validator("triggered_at", "acknowledged_at", "resolved_at", "created_at", "updated_at", mode="before")
    @classmethod
    def parse_datetime(cls, value: str | datetime | None) -> Optional[datetime]:
        if value is None:
            return None

        if isinstance(value, datetime):
            return value

        try:
            if "T" in value:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid datetime format: {value}") from e
    
    class Config:
        from_attributes = True