from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime, timezone
from ..core.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(String)
    log_path = Column(String)
    is_alert = Column(Integer, default=0)  # 0 for False, 1 for True
    framework_type = Column(String, default="laravel")
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )
