from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime, timezone
from ..core.database import Base


class ServiceWorker(Base):
    __tablename__ = "service_workers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    status = Column(String)
    is_monitoring = Column(Integer, default=0)  # 0 for False, 1 for True
    is_enabled = Column(Integer, default=0)  # 0 for False, 1 for True
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )
