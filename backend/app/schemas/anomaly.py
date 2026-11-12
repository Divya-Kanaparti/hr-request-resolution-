"""
Anomaly Schemas
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class AnomalyResponse(BaseModel):
    anomaly_id: str
    ticket_id: str
    anomaly_type: str
    severity: str
    detected_at: datetime
    description: str
    status: str
    ground_truth_label: bool
    ticket_title: Optional[str] = None
    ticket_tracking: Optional[str] = None

    class Config:
        from_attributes = True

class AnomalyResolveRequest(BaseModel):
    status: str = "RESOLVED"
    resolution_comment: Optional[str] = None

