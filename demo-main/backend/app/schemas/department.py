"""
Department Schemas
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class DepartmentBase(BaseModel):
    name: str
    code: str
    location: Optional[str] = "Headquarters"

class DepartmentCreate(DepartmentBase):
    manager_id: Optional[str] = None

class DepartmentResponse(DepartmentBase):
    dept_id: str
    manager_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

