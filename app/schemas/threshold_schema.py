from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional
from enum import Enum

class ThresholdTypeEnum(str, Enum):
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"

class ThresholdConditionEnum(str, Enum):
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    EQUALS = "equals"

class ThresholdSeverityEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ThresholdBase(BaseModel):
    name: str
    description: Optional[str] = None
    metric_type: ThresholdTypeEnum
    condition: ThresholdConditionEnum = ThresholdConditionEnum.GREATER_THAN
    threshold_value: float
    duration_minutes: int = 1
    severity: ThresholdSeverityEnum = ThresholdSeverityEnum.MEDIUM
    source_filter: Optional[str] = None
    cooldown_minutes: int = 5
    
    @field_validator("threshold_value")
    @classmethod
    def validate_threshold_value(cls, v: float) -> float:
        if v < 0 or v > 100:
            raise ValueError("Threshold value must be between 0 and 100")
        return v
    
    @field_validator("duration_minutes")
    @classmethod
    def validate_duration_minutes(cls, v: int) -> int:
        if v < 1 or v > 60:
            raise ValueError("Duration must be between 1 and 60 minutes")
        return v
    
    @field_validator("cooldown_minutes")
    @classmethod
    def validate_cooldown_minutes(cls, v: int) -> int:
        if v < 0 or v > 120:
            raise ValueError("Cooldown must be between 0 and 120 minutes")
        return v

class ThresholdCreate(ThresholdBase):
    is_enabled: bool = True

class ThresholdUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    metric_type: Optional[ThresholdTypeEnum] = None
    condition: Optional[ThresholdConditionEnum] = None
    threshold_value: Optional[float] = None
    duration_minutes: Optional[int] = None
    severity: Optional[ThresholdSeverityEnum] = None
    is_enabled: Optional[bool] = None
    source_filter: Optional[str] = None
    cooldown_minutes: Optional[int] = None
    
    @field_validator("threshold_value")
    @classmethod
    def validate_threshold_value(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and (v < 0 or v > 100):
            raise ValueError("Threshold value must be between 0 and 100")
        return v
    
    @field_validator("duration_minutes")
    @classmethod
    def validate_duration_minutes(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v < 1 or v > 60):
            raise ValueError("Duration must be between 1 and 60 minutes")
        return v
    
    @field_validator("cooldown_minutes")
    @classmethod
    def validate_cooldown_minutes(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v < 0 or v > 120):
            raise ValueError("Cooldown must be between 0 and 120 minutes")
        return v

class ThresholdResponse(ThresholdBase):
    id: int
    is_enabled: bool
    created_at: datetime
    updated_at: datetime
    
    @field_validator("created_at", "updated_at", mode="before")
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

class ThresholdToggle(BaseModel):
    is_enabled: bool