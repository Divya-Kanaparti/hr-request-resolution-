"""
Authentication Pydantic Schemas
"""
from typing import Optional
from pydantic import BaseModel, EmailStr

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserSummary"

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    department_id: str
    role: Optional[str] = "EMPLOYEE"
    employment_type: Optional[str] = "FULL_TIME"

class UserSummary(BaseModel):
    emp_id: str
    email: str
    full_name: str
    department_id: str
    role: str
    employment_type: str
    status: str

    class Config:
        from_attributes = True

TokenResponse.model_rebuild()

