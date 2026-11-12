"""
Assignment Schemas
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class AssignmentBase(BaseModel):
    assigned_to_id: str
    tier: str = "TIER_1"
    reason: Optional[str] = None

class AssignmentCreate(AssignmentBase):
    pass

class AssignmentResponse(AssignmentBase):
    assignment_id: str
    ticket_id: str
    assigned_by_id: str
    assigned_at: datetime
    unassigned_at: Optional[datetime] = None
    is_active: bool
    assigned_to_name: Optional[str] = None
    assigned_by_name: Optional[str] = None

    class Config:
        from_attributes = True

