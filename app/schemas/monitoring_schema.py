from typing import List, Dict, Optional,Any
from pydantic import BaseModel
from datetime import datetime


class LogEntry(BaseModel):
    timestamp: datetime
    level: str
    message: str
    context: Optional[str] = None
    controller: Optional[str] = None
    line_number: Optional[int] = None
    file_path: Optional[str] = None


class SystemMetrics(BaseModel):
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_available: int
    disk_usage: Dict[str, dict]

class ServiceStatus(BaseModel):
    name: str
    status: str
    active: bool
    enabled: bool
    uptime: Optional[str] = None
class MonitoringData(BaseModel):
    timestamp: datetime
    logs: Dict[str, List[LogEntry]]
    system_metrics: SystemMetrics
    services: List[ServiceStatus]
    
