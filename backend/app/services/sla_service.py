"""
SLA Service
Calculates and updates SLA metrics, monitors deadlines, and flags breaches.
"""
from datetime import datetime
from typing import Tuple, List, Optional
from sqlalchemy.orm import Session
from app.models.sla import SLA
from app.models.ticket import Ticket, TicketStatusEnum
from app.core.business_hours import (
    calculate_sla_deadlines,
    calculate_business_hours_between,
    add_business_hours
)
from app.services.audit_service import log_audit_event
import uuid

def initialize_ticket_sla(
    db: Session,
    ticket: Ticket,
    created_at: Optional[datetime] = None
) -> SLA:
    """Initialize SLA record when ticket is created."""
    base_time = created_at or ticket.created_at or datetime.utcnow()
    resp_due, res_due, limit_hours = calculate_sla_deadlines(base_time, ticket.priority.value if hasattr(ticket.priority, "value") else str(ticket.priority))
    
    sla_id = f"SLA-{uuid.uuid4().hex[:10].upper()}"
    sla = SLA(
        sla_id=sla_id,
        ticket_id=ticket.ticket_id,
        priority=ticket.priority,
        business_hours_limit=limit_hours,
        response_due_at=resp_due,
        resolution_due_at=res_due,
        first_response_at=None,
        is_response_breached=False,
        is_resolution_breached=False,
        calculated_business_hours=0.00
    )
    db.add(sla)
    db.commit()
    db.refresh(sla)
    return sla

def record_first_response(db: Session, ticket_id: str, response_time: Optional[datetime] = None) -> Optional[SLA]:
    """Record first agent response time and check for response SLA breach."""
    sla = db.query(SLA).filter(SLA.ticket_id == ticket_id).first()
    if not sla or sla.first_response_at is not None:
        return sla

    now = response_time or datetime.utcnow()
    sla.first_response_at = now
    if now > sla.response_due_at:
        sla.is_response_breached = True
    db.commit()
    db.refresh(sla)
    return sla

def refresh_sla_status(db: Session, ticket: Ticket, now: Optional[datetime] = None) -> SLA:
    """Check and update SLA breach status and elapsed business hours."""
    current_time = now or datetime.utcnow()
    sla = db.query(SLA).filter(SLA.ticket_id == ticket.ticket_id).first()
    if not sla:
        return initialize_ticket_sla(db, ticket, ticket.created_at)

    # Calculate business hours elapsed
    end_point = ticket.resolved_at if ticket.status in [TicketStatusEnum.RESOLVED, TicketStatusEnum.CLOSED] and ticket.resolved_at else current_time
    elapsed = calculate_business_hours_between(ticket.created_at, end_point)
    sla.calculated_business_hours = elapsed

    # Check response breach if not yet responded
    if not sla.first_response_at and current_time > sla.response_due_at:
        sla.is_response_breached = True

    # Check resolution breach
    if ticket.status in [TicketStatusEnum.RESOLVED, TicketStatusEnum.CLOSED] and ticket.resolved_at:
        if ticket.resolved_at > sla.resolution_due_at:
            sla.is_resolution_breached = True
    else:
        if current_time > sla.resolution_due_at:
            sla.is_resolution_breached = True

    db.commit()
    db.refresh(sla)
    return sla

def scan_all_active_slas(db: Session) -> Tuple[int, int, List[str]]:
    """Scan all open tickets and update their SLA breach states."""
    active_tickets = db.query(Ticket).filter(
        Ticket.status.notin_([TicketStatusEnum.RESOLVED, TicketStatusEnum.CLOSED])
    ).all()

    breached_count = 0
    updated_ids = []
    now = datetime.utcnow()

    for ticket in active_tickets:
        sla = refresh_sla_status(db, ticket, now)
        if sla.is_resolution_breached or sla.is_response_breached:
            breached_count += 1
            updated_ids.append(ticket.ticket_id)

    return len(active_tickets), breached_count, updated_ids

