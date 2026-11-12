"""
Analytics and Reporting API Routes
"""
from typing import List, Dict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.session import get_db
from app.models.ticket import Ticket, TicketStatusEnum
from app.models.employee import Employee, RoleEnum
from app.models.category import Category
from app.models.policy import PolicyDocument
from app.models.sla import SLA
from app.models.resolution import Resolution
from app.models.anomaly import AnomalyRecord, AnomalyStatusEnum
from app.schemas.analytics import (
    DashboardSummaryResponse, CategoryDistribution,
    SLAComplianceMetrics, AgentWorkload
)
from app.core.rbac import require_roles, Role, HR_STAFF_ROLES

router = APIRouter(prefix="/analytics", tags=["Analytics & Reports"])

@router.get("/summary", response_model=DashboardSummaryResponse, summary="Executive Dashboard Summary")
def get_analytics_summary(
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(HR_STAFF_ROLES))
):
    """Retrieve top-level KPI metrics for dashboards."""
    total_t = db.query(func.count(Ticket.ticket_id)).scalar() or 0
    resolved_t = db.query(func.count(Ticket.ticket_id)).filter(Ticket.status.in_([TicketStatusEnum.RESOLVED, TicketStatusEnum.CLOSED])).scalar() or 0
    open_t = total_t - resolved_t
    clarification_t = db.query(func.count(Ticket.ticket_id)).filter(Ticket.status == TicketStatusEnum.CLARIFICATION_NEEDED).scalar() or 0
    escalated_t = db.query(func.count(Ticket.ticket_id)).filter(Ticket.status == TicketStatusEnum.ESCALATED).scalar() or 0
    sensitive_t = db.query(func.count(Ticket.ticket_id)).filter(Ticket.is_sensitive == True).scalar() or 0
    
    breached_t = db.query(func.count(SLA.sla_id)).filter(SLA.is_resolution_breached == True).scalar() or 0
    compliance_rate = round(((total_t - breached_t) / total_t * 100), 1) if total_t > 0 else 100.0

    # Avg resolution hours
    avg_hours = db.query(func.avg(SLA.calculated_business_hours)).scalar() or 0.0

    total_emp = db.query(func.count(Employee.emp_id)).scalar() or 0
    active_pol = db.query(func.count(PolicyDocument.policy_id)).scalar() or 0
    total_anom = db.query(func.count(AnomalyRecord.anomaly_id)).scalar() or 0

    return DashboardSummaryResponse(
        total_tickets=total_t,
        open_tickets=open_t,
        resolved_tickets=resolved_t,
        clarification_needed_tickets=clarification_t,
        escalated_tickets=escalated_t,
        sensitive_tickets=sensitive_t,
        sla_breached_tickets=breached_t,
        sla_compliance_rate=compliance_rate,
        avg_resolution_hours=round(float(avg_hours), 1),
        total_employees=total_emp,
        active_policies=active_pol,
        total_anomalies=total_anom
    )

@router.get("/category-trends", response_model=List[CategoryDistribution], summary="Category Distribution")
def get_category_trends(
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(HR_STAFF_ROLES))
):
    """Breakdown of ticket volume by category."""
    total_t = db.query(func.count(Ticket.ticket_id)).scalar() or 1
    categories = db.query(Category).all()
    results = []

    for cat in categories:
        count = db.query(func.count(Ticket.ticket_id)).filter(Ticket.category_id == cat.category_id).scalar() or 0
        pct = round((count / total_t) * 100, 1)
        results.append(CategoryDistribution(
            category_id=cat.category_id,
            category_name=cat.name,
            ticket_count=count,
            percentage=pct
        ))
    results.sort(key=lambda x: x.ticket_count, reverse=True)
    return results

@router.get("/agent-workload", response_model=List[AgentWorkload], summary="Agent Workload and Ratings")
def get_agent_workload(
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(HR_STAFF_ROLES))
):
    """Workload, performance and satisfaction ratings across HR staff."""
    agents = db.query(Employee).filter(Employee.role.in_([RoleEnum.HR_AGENT, RoleEnum.HR_MANAGER])).all()
    results = []

    for ag in agents:
        # Active assignments
        active_count = db.query(func.count(Ticket.ticket_id)).join(Ticket.assignments).filter(
            Ticket.assignments.any(assigned_to_id=ag.emp_id, is_active=True),
            Ticket.status.notin_([TicketStatusEnum.RESOLVED, TicketStatusEnum.CLOSED])
        ).scalar() or 0

        # Resolved
        resolved_count = db.query(func.count(Resolution.resolution_id)).filter(
            Resolution.resolved_by_id == ag.emp_id
        ).scalar() or 0

        # Avg rating
        avg_r = db.query(func.avg(Resolution.employee_rating)).filter(
            Resolution.resolved_by_id == ag.emp_id,
            Resolution.employee_rating.isnot(None)
        ).scalar()

        # Breached count
        breached_c = db.query(func.count(Ticket.ticket_id)).join(SLA).join(Ticket.assignments).filter(
            Ticket.assignments.any(assigned_to_id=ag.emp_id),
            SLA.is_resolution_breached == True
        ).scalar() or 0

        results.append(AgentWorkload(
            agent_id=ag.emp_id,
            agent_name=ag.full_name,
            active_tickets=active_count,
            resolved_tickets=resolved_count,
            avg_rating=round(float(avg_r), 2) if avg_r else None,
            breached_count=breached_c
        ))
    return results

