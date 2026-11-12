"""
SLA Schemas
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class SLABase(BaseModel):
    priority: str
    business_hours_limit: int

class SLAResponse(SLABase):
    sla_id: str
    ticket_id: str
    response_due_at: datetime
    resolution_due_at: datetime
    first_response_at: Optional[datetime] = None
    is_response_breached: bool
    is_resolution_breached: bool
    calculated_business_hours: float
    created_at: datetime
    hours_remaining: Optional[float] = None

    class Config:
        from_attributes = True

class SLACheckResult(BaseModel):
    checked_count: int
    breached_count: int
    updated_tickets: list

