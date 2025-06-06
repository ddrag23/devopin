
from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar('T')
class AdapterListResponse(BaseModel, Generic[T]):
    page: Optional[int]
    limit: Optional[int]
    total: int
    data: List[T]

    class Config:
        from_attributes = True
