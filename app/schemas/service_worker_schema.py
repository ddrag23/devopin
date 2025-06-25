from pydantic import BaseModel, field_validator
from fastapi import Form
from datetime import datetime
from typing import Optional


# User
class ServiceWorkerBase(BaseModel):
    name: str
    description: Optional[str] = None
    


class ServiceWorkerCreate(ServiceWorkerBase):
    @classmethod
    def as_form(
        cls,
        name: str = Form(...),
        description: Optional[str] = Form(None),
    ):
        return cls(
            name=name,
            description=description,
        )

class ServiceWorkerUpdateAgent(ServiceWorkerBase):
    is_monitoring: Optional[bool] = None
    is_enabled: Optional[bool] = None
    status: Optional[str] = None

    @classmethod
    def as_form(
        cls,
        name: str = Form(...),
        is_monitoring: bool = Form(False),
        is_enabled: bool = Form(False),
        status: Optional[str] = Form(None),
        description: Optional[str] = Form(None),
    ):
        return cls(
            name=name,
            description=description,
            is_monitoring=is_monitoring,
            is_enabled=is_enabled,
            status=status,
        )


class ServiceWorkerResponse(ServiceWorkerBase):
    id: int
    status: Optional[str] = None  # Status bisa None jika tidak ada
    is_monitoring: Optional[bool]
    is_enabled: Optional[bool]
    created_at: datetime
    updated_at: datetime

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def parse_datetime(cls, value: str | datetime | None) -> datetime:
        if value is None:
            return datetime.now()  # Nilai default jika None

        if isinstance(value, datetime):
            return value  # Langsung kembalikan jika sudah datetime

        try:
            # Handle berbagai format string
            if "T" in value:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid datetime format: {value}") from e

    class Config:
        from_attributes = True
