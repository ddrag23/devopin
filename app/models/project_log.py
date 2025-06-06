from sqlalchemy import Column, Integer, String, DateTime,ForeignKey
from datetime import datetime,timezone
from app.core.database import Base

class ProjectLog(Base):
    __tablename__ = "project_logs"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer,ForeignKey("projects.id"),index=True,nullable=False)
    log_level = Column(String,nullable=False)
    message = Column(String,nullable=False)
    log_time = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
