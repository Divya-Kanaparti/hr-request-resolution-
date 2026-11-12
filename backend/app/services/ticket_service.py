"""
Ticket Service
Handles ticket lifecycle, assignments, escalations, messaging, and resolution.
"""
from datetime import datetime
from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.ticket import Ticket, TicketStatusEnum
from app.models.employee import Employee, RoleEnum
from app.models.category import Category, PriorityEnum, TierEnum
from app.models.assignment import Assignment
from app.models.message import Message, MessageTypeEnum
from app.models.resolution import Resolution, ResolutionTypeEnum
from app.schemas.ticket import TicketCreate, TicketAssignRequest, TicketEscalateRequest
from app.schemas.resolution import ResolutionCreate, SatisfactionRatingRequest
from app.services.classification_service import classify_text, detect_ambiguity
from app.services.sla_service import initialize_ticket_sla, record_first_response, refresh_sla_status
from app.services.audit_service import log_audit_event
from app.core.id_conventions import generate_message_id, generate_ticket_id
import uuid

def generate_tracking_number(db: Session) -> str:
    """Generate sequential enterprise tracking number like REQ-2026-0001."""
    count = db.query(func.count(Ticket.ticket_id)).scalar() or 0
    return f"REQ-2026-{(count + 1):04d}"

def get_next_agent_for_assignment(db: Session, is_sensitive: bool = False) -> Optional[Employee]:
    """Find least-loaded eligible HR staff member."""
    if is_sensitive:
        # Assign to HR Manager or Compliance Officer
        return db.query(Employee).filter(
            Employee.role.in_([RoleEnum.HR_MANAGER, RoleEnum.COMPLIANCE_OFFICER]),
            Employee.is_active == True
        ).first()

    # Regular agent with least active assignments
    agents = db.query(Employee).filter(
        Employee.role.in_([RoleEnum.HR_AGENT, RoleEnum.HR_MANAGER]),
        Employee.is_active == True
    ).all()
    if not agents:
        return None
    return agents[0]

def create_ticket(db: Session, employee: Employee, ticket_in: TicketCreate) -> Ticket:
    """Create a new HR request ticket with AI classification, ambiguity check, and SLA initialization."""
    # 1. Classification & Ambiguity Detection
    classification = classify_text(ticket_in.title, ticket_in.description)
    category_id = ticket_in.category_id or classification.recommended_category_id
    
    category = db.query(Category).filter(Category.category_id == category_id).first()
    category_name = category.name if category else classification.category_name

    ambiguity = detect_ambiguity(ticket_in.title, ticket_in.description, category_name)
    is_sensitive = ticket_in.is_sensitive or classification.is_sensitive
    priority_val = ticket_in.priority or classification.recommended_priority

    # Initial Status
    initial_status = TicketStatusEnum.CLARIFICATION_NEEDED if ambiguity.is_ambiguous else TicketStatusEnum.NEW

    ticket_id = generate_ticket_id(db)
    tracking_num = generate_tracking_number(db)

    ticket = Ticket(
        ticket_id=ticket_id,
        tracking_number=tracking_num,
        employee_id=employee.emp_id,
        category_id=category_id,
        title=ticket_in.title,
        description=ticket_in.description,
        status=initial_status,
        priority=PriorityEnum[priority_val] if priority_val in PriorityEnum.__members__ else PriorityEnum.MEDIUM,
        is_sensitive=is_sensitive,
        confidential_assigned_to=None
    )
    db.add(ticket)
    db.flush()

    # 2. Assignment / Confidential Routing
    assigned_agent = get_next_agent_for_assignment(db, is_sensitive=is_sensitive)
    if is_sensitive and assigned_agent:
        ticket.confidential_assigned_to = assigned_agent.emp_id

    if assigned_agent:
        asg = Assignment(
            assignment_id=f"ASG-{uuid.uuid4().hex[:10].upper()}",
            ticket_id=ticket.ticket_id,
            assigned_to_id=assigned_agent.emp_id,
            assigned_by_id=employee.emp_id,
            tier=TierEnum.TIER_2 if is_sensitive else TierEnum.TIER_1,
            reason="Confidential routing" if is_sensitive else "Automated triage assignment",
            is_active=True
        )
        db.add(asg)

    # 3. Initialize SLA
    initialize_ticket_sla(db, ticket)

    # 4. If ambiguous, post system clarification message
    if ambiguity.is_ambiguous and ambiguity.clarification_prompt:
        clarification_msg = Message(
            message_id=generate_message_id(db, ticket.ticket_id),
            ticket_id=ticket.ticket_id,
            sender_id=employee.emp_id,
            message_type=MessageTypeEnum.CLARIFICATION_PROMPT,
            content=f"System Notice: {ambiguity.clarification_prompt}",
            is_internal=False
        )
        db.add(clarification_msg)

    # Commit and audit
    db.commit()
    db.refresh(ticket)
    log_audit_event(
        db=db,
        entity_type="TICKET",
        entity_id=ticket.ticket_id,
        action="CREATE_TICKET",
        actor_id=employee.emp_id,
        details={"tracking_number": ticket.tracking_number, "is_sensitive": is_sensitive, "status": ticket.status.value}
    )
    return ticket

def assign_ticket(
    db: Session,
    ticket_id: str,
    assigned_to_id: str,
    assigned_by: Employee,
    tier: str = "TIER_1",
    reason: Optional[str] = None
) -> Assignment:
    """Assign or reassign a ticket to an HR agent."""
    ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    target_agent = db.query(Employee).filter(Employee.emp_id == assigned_to_id).first()
    if not target_agent:
        raise HTTPException(status_code=404, detail="Assigned agent not found")

    # Deactivate existing active assignments
    for old_asg in ticket.assignments:
        if old_asg.is_active:
            old_asg.is_active = False
            old_asg.unassigned_at = datetime.utcnow()

    new_asg = Assignment(
        assignment_id=f"ASG-{uuid.uuid4().hex[:10].upper()}",
        ticket_id=ticket.ticket_id,
        assigned_to_id=target_agent.emp_id,
        assigned_by_id=assigned_by.emp_id,
        tier=TierEnum[tier] if tier in TierEnum.__members__ else TierEnum.TIER_1,
        reason=reason or "Manual reassignment",
        is_active=True
    )
    db.add(new_asg)

    # If ticket was sensitive, update confidential assignment
    if ticket.is_sensitive:
        ticket.confidential_assigned_to = target_agent.emp_id

    # If ticket was NEW, advance to IN_PROGRESS
    if ticket.status == TicketStatusEnum.NEW:
        ticket.status = TicketStatusEnum.IN_PROGRESS

    db.commit()
    db.refresh(new_asg)
    log_audit_event(
        db=db,
        entity_type="TICKET",
        entity_id=ticket.ticket_id,
        action="ASSIGN_TICKET",
        actor_id=assigned_by.emp_id,
        details={"assigned_to": target_agent.full_name, "tier": tier, "reason": reason}
    )
    return new_asg

def escalate_ticket(
    db: Session,
    ticket_id: str,
    actor: Employee,
    request: TicketEscalateRequest
) -> Ticket:
    """Escalate a ticket to Tier 2 or Tier 3 / Management."""
    ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    target_tier = request.target_tier.upper()
    ticket.status = TicketStatusEnum.ESCALATED

    # Reassign if target provided
    if request.assigned_to_id:
        assign_ticket(
            db=db,
            ticket_id=ticket.ticket_id,
            assigned_to_id=request.assigned_to_id,
            assigned_by=actor,
            tier=target_tier,
            reason=f"Escalation: {request.escalation_reason}"
        )

    # Add audit log and internal message
    system_msg = Message(
        message_id=generate_message_id(db, ticket.ticket_id),
        ticket_id=ticket.ticket_id,
        sender_id=actor.emp_id,
        message_type=MessageTypeEnum.SYSTEM_EVENT,
        content=f"Ticket escalated to {target_tier}. Reason: {request.escalation_reason}",
        is_internal=True
    )
    db.add(system_msg)
    db.commit()
    db.refresh(ticket)

    log_audit_event(
        db=db,
        entity_type="TICKET",
        entity_id=ticket.ticket_id,
        action="ESCALATE_TICKET",
        actor_id=actor.emp_id,
        details={"target_tier": target_tier, "reason": request.escalation_reason}
    )
    return ticket

def resolve_ticket(
    db: Session,
    ticket_id: str,
    actor: Employee,
    resolution_in: ResolutionCreate
) -> Resolution:
    """Resolve a ticket, record resolution notes, root cause, and refresh SLA."""
    ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    now = datetime.utcnow()
    ticket.status = TicketStatusEnum.RESOLVED
    ticket.resolved_at = now

    resolution_id = f"RES-{uuid.uuid4().hex[:10].upper()}"
    res_type = ResolutionTypeEnum[resolution_in.resolution_type] if resolution_in.resolution_type in ResolutionTypeEnum.__members__ else ResolutionTypeEnum.POLICY_EXPLANATION

    resolution = Resolution(
        resolution_id=resolution_id,
        ticket_id=ticket.ticket_id,
        resolved_by_id=actor.emp_id,
        resolution_type=res_type,
        resolution_notes=resolution_in.resolution_notes,
        root_cause=resolution_in.root_cause,
        policy_version_used_id=resolution_in.policy_version_used_id,
        resolved_at=now
    )
    db.add(resolution)

    # Refresh SLA final metrics
    refresh_sla_status(db, ticket, now)

    # Add resolution message
    close_msg = Message(
        message_id=generate_message_id(db, ticket.ticket_id),
        ticket_id=ticket.ticket_id,
        sender_id=actor.emp_id,
        message_type=MessageTypeEnum.AGENT_REPLY,
        content=f"Resolution Provided:\n{resolution_in.resolution_notes}",
        is_internal=False
    )
    db.add(close_msg)

    db.commit()
    db.refresh(resolution)

    log_audit_event(
        db=db,
        entity_type="TICKET",
        entity_id=ticket.ticket_id,
        action="RESOLVE_TICKET",
        actor_id=actor.emp_id,
        details={"resolution_type": resolution.resolution_type.value, "root_cause": resolution.root_cause}
    )
    return resolution

def add_message(
    db: Session,
    ticket_id: str,
    sender: Employee,
    content: str,
    message_type: str = "EMPLOYEE_NOTE",
    is_internal: bool = False,
    citations_json: Optional[Any] = None
) -> Message:
    """Add a message to the ticket conversation thread."""
    ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    msg_type = MessageTypeEnum[message_type] if message_type in MessageTypeEnum.__members__ else MessageTypeEnum.EMPLOYEE_NOTE

    msg = Message(
        message_id=generate_message_id(db, ticket.ticket_id),
        ticket_id=ticket.ticket_id,
        sender_id=sender.emp_id,
        message_type=msg_type,
        content=content,
        is_internal=is_internal,
        citations_json=citations_json
    )
    db.add(msg)

    # If first response by agent, record in SLA
    if sender.role in [RoleEnum.HR_AGENT.value, RoleEnum.HR_MANAGER.value, RoleEnum.ADMIN.value] and not is_internal:
        record_first_response(db, ticket.ticket_id)
        if ticket.status == TicketStatusEnum.NEW:
            ticket.status = TicketStatusEnum.IN_PROGRESS

    # If employee replied to a ticket awaiting clarification, resume progress
    if sender.emp_id == ticket.employee_id and ticket.status == TicketStatusEnum.CLARIFICATION_NEEDED:
        ticket.status = TicketStatusEnum.IN_PROGRESS

    db.commit()
    db.refresh(msg)
    return msg

