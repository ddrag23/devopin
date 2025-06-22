from pydantic import BaseModel, field_validator
from fastapi import Form
from datetime import datetime
from typing import Dict, Any


class SystemMetricBase(BaseModel):
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_available: int
    disk_usage: Dict[str, Any]  # Karena JSON-nya fleksibel

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


class SystemMetricCreate(SystemMetricBase):
    @classmethod
    def as_form(
        cls,
        timestamp: datetime = Form(...),
        cpu_percent: float = Form(...),
        memory_percent: float = Form(...),
        memory_available: int = Form(...),
        disk_usage: str = Form(...)  # Dikirim sebagai JSON string
    ):
        import json
        return cls(
            timestamp=timestamp,
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_available=memory_available,
            disk_usage=json.loads(disk_usage),
        )


class SystemMetricResponse(SystemMetricBase):
    id: int

    class Config:
        from_attributes = True
