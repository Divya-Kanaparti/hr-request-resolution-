"""
Analytics and Reporting Schemas
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class DashboardSummaryResponse(BaseModel):
    total_tickets: int
    open_tickets: int
    resolved_tickets: int
    clarification_needed_tickets: int
    escalated_tickets: int
    sensitive_tickets: int
    sla_breached_tickets: int
    sla_compliance_rate: float
    avg_resolution_hours: float
    total_employees: int
    active_policies: int
    total_anomalies: int

class CategoryDistribution(BaseModel):
    category_id: str
    category_name: str
    ticket_count: int
    percentage: float

class StatusDistribution(BaseModel):
    status: str
    count: int

class PriorityDistribution(BaseModel):
    priority: str
    count: int

class SLAComplianceMetrics(BaseModel):
    total_sla_tracked: int
    met_sla_count: int
    breached_sla_count: int
    compliance_percentage: float
    by_priority: Dict[str, float]

class AgentWorkload(BaseModel):
    agent_id: str
    agent_name: str
    active_tickets: int
    resolved_tickets: int
    avg_rating: Optional[float] = None
    breached_count: int

class AnomalySummary(BaseModel):
    anomaly_type: str
    count: int
    unresolved_count: int

