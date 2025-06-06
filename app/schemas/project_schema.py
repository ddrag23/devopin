from pydantic import BaseModel, field_validator
from fastapi import Form
from datetime import datetime
from typing import Optional


# User
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    log_path: str
    is_alert: Optional[bool] = False
    framework_type: str


class ProjectCreate(ProjectBase):
    @classmethod
    def as_form(
        cls,
        name: str = Form(...),
        description: Optional[str] = Form(None),
        log_path: str = Form(...),
        is_alert: Optional[bool] = Form(0),
        framework_type: str = Form(...),
    ):
        return cls(
            name=name,
            description=description,
            log_path=log_path,
            is_alert=is_alert,
            framework_type=framework_type,
        )


class ProjectResponse(ProjectBase):
    id: int
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
