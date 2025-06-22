from pydantic import BaseModel, field_validator
from fastapi import Form
from datetime import datetime
from typing import Dict, Any


class SystemMetricBase(BaseModel):
    cpu_percent: float
    memory_percent: float
    memory_available: int
    pass

class SystemMetricCreate(SystemMetricBase):
    disk_usage: Dict[str, Any]  # Karena JSON-nya fleksibel
    timestamp: datetime
    @field_validator("timestamp", mode="before")
    @classmethod
    def parse_datetime(cls, value: str | datetime | None) -> datetime:
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
    pass


class SystemMetricResponse(SystemMetricBase):
    id: int
    disk_usage: str  # Karena JSON-nya fleksibel
    timestamp_log : datetime
    @field_validator("timestamp_log", mode="before")
    @classmethod
    def parse_datetime(cls, value: str | datetime | None) -> datetime:
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
    class Config:
        from_attributes = True
