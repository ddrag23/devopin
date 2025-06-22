
from sqlalchemy import Column, Integer, Float, DateTime,Text
from datetime import datetime,timezone
from app.core.database import Base

class SystemMetric(Base):
    __tablename__ = "system_metrics"
    id = Column(Integer, primary_key=True, index=True)
    cpu_percent = Column(Float)
    memory_percent = Column(Float)
    memory_available = Column(Integer)
    disk_usage = Column(Text)
    timestamp_log = Column(DateTime, default=datetime.now(timezone.utc))
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

