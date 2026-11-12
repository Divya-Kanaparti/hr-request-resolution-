"""
Ticket Schemas
"""
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel
from app.schemas.assignment import AssignmentResponse
from app.schemas.sla import SLAResponse
from app.schemas.message import MessageResponse
from app.schemas.resolution import ResolutionResponse

class TicketBase(BaseModel):
    category_id: str
    title: str
    description: str
    priority: Optional[str] = "MEDIUM"
    is_sensitive: Optional[bool] = False

class TicketCreate(TicketBase):
    pass

class TicketUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    is_sensitive: Optional[bool] = None
    confidential_assigned_to: Optional[str] = None

class TicketAssignRequest(BaseModel):
    assigned_to_id: str
    tier: Optional[str] = "TIER_1"
    reason: Optional[str] = "Routine assignment"

class TicketEscalateRequest(BaseModel):
    assigned_to_id: Optional[str] = None
    target_tier: str = "TIER_2"
    escalation_reason: str

class ClassificationResult(BaseModel):
    recommended_category_id: str
    category_name: str
    confidence: float
    is_sensitive: bool
    sensitivity_reason: Optional[str] = None
    recommended_priority: str
    detected_keywords: List[str] = []

class AmbiguityCheckResult(BaseModel):
    is_ambiguous: bool
    ambiguity_reasons: List[str] = []
    missing_fields: List[str] = []
    clarification_prompt: Optional[str] = None

class TicketResponse(TicketBase):
    ticket_id: str
    tracking_number: str
    employee_id: str
    employee_name: Optional[str] = None
    category_name: Optional[str] = None
    status: str
    priority: str
    is_sensitive: bool
    confidential_assigned_to: Optional[str] = None
    assigned_agent_name: Optional[str] = None
    current_tier: Optional[str] = "TIER_1"
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    sla_status: Optional[str] = "ON_TRACK"
    resolution_due_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AnomalyResponse(BaseModel):
    anomaly_id: str
    ticket_id: str
    anomaly_type: str
    severity: str
    detected_at: datetime
    description: str
    status: str
    ground_truth_label: Optional[bool] = None
    # ground_truth_label: Optional[str] = None

    class Config:
        from_attributes = True


class TicketDetailResponse(TicketResponse):
    sla: Optional[SLAResponse] = None
    assignments: List[AssignmentResponse] = []
    messages: List[MessageResponse] = []
    resolution: Optional[ResolutionResponse] = None
    has_active_anomalies: bool = False
    anomalies: List[AnomalyResponse] = []

# class TicketDetailResponse(TicketResponse):
#     sla: Optional[SLAResponse] = None
#     assignments: List[AssignmentResponse] = []
#     messages: List[MessageResponse] = []
#     resolution: Optional[ResolutionResponse] = None
#     has_active_anomalies: bool = False
#     anomalies: List[Any] = []

