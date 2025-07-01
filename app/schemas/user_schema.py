from pydantic import BaseModel
from fastapi import Form
from datetime import datetime
from typing import List,Optional
# User
class UserBase(BaseModel):
    name: str
    email: str
    user_timezone: Optional[str] = 'UTC'
    
class UserCreate(UserBase):
    password: str
    @classmethod
    def as_form(
        cls,
        name: str = Form(...),
        email: str = Form(...),
        password: str = Form(...),
        user_timezone: str = Form('UTC'),
    ):
        return cls(name=name,email=email, password=password, user_timezone=user_timezone)
    
class User(UserBase):
    id:int
    class Config:
        from_attributes = True

class UserResponse(User):
    created_at: datetime
    updated_at: datetime
