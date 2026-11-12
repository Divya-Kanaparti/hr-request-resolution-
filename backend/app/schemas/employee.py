"""
Employee Schemas
"""
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, EmailStr

class EmployeeBase(BaseModel):
    email: EmailStr
    full_name: str
    department_id: str
    role: str = "EMPLOYEE"
    employment_type: str = "FULL_TIME"
    status: str = "ACTIVE"
    is_active: bool = True

class EmployeeCreate(EmployeeBase):
    password: str
    hire_date: Optional[date] = None

class EmployeeUpdate(BaseModel):
    full_name: Optional[str] = None
    department_id: Optional[str] = None
    role: Optional[str] = None
    employment_type: Optional[str] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None

class EmployeeResponse(EmployeeBase):
    emp_id: str
    hire_date: date
    created_at: datetime
    department_name: Optional[str] = None

    class Config:
        from_attributes = True

