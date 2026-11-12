"""
Tickets API Routes
Complete lifecycle endpoints for HR Request submission, triage, messaging, and resolution.
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.ticket import Ticket, TicketStatusEnum
from app.models.employee import Employee, RoleEnum
from app.models.category import Category
from app.models.assignment import Assignment
from app.models.sla import SLA
from app.models.message import Message, MessageTypeEnum
from app.models.resolution import Resolution
from app.schemas.ticket import (
    TicketCreate, TicketUpdate, TicketResponse, TicketDetailResponse,
    TicketAssignRequest, TicketEscalateRequest,
    ClassificationResult, AmbiguityCheckResult
)
from app.schemas.message import MessageCreate, MessageResponse
from app.schemas.resolution import ResolutionCreate, ResolutionResponse, SatisfactionRatingRequest
from app.core.rbac import (
    get_current_user, require_roles, Role, HR_STAFF_ROLES,
    TICKET_RESOLVER_ROLES, can_access_ticket
)
from app.services.ticket_service import (
    create_ticket,
    assign_ticket,
    escalate_ticket,
    resolve_ticket,
    add_message
)
from app.services.classification_service import classify_text, detect_ambiguity
from app.services.sla_service import refresh_sla_status

router = APIRouter(prefix="/tickets", tags=["Tickets"])

def format_ticket_summary(t: Ticket, db: Session) -> TicketResponse:
    """Helper to convert Ticket ORM to response schema with enriched relations."""
    assigned_name = None
    active_asg = next((a for a in t.assignments if a.is_active), None)
    if active_asg and active_asg.assigned_to:
        assigned_name = active_asg.assigned_to.full_name
    elif t.confidential_assigned_to:
        agent = db.query(Employee).filter(Employee.emp_id == t.confidential_assigned_to).first()
        if agent:
            assigned_name = f"{agent.full_name} (Confidential)"

    sla_status = "ON_TRACK"
    res_due = None
    if t.sla:
        res_due = t.sla.resolution_due_at
        if t.sla.is_resolution_breached:
            sla_status = "BREACHED"
        elif datetime.utcnow() > t.sla.resolution_due_at:
            sla_status = "BREACHED"

    return TicketResponse(
        ticket_id=t.ticket_id,
        tracking_number=t.tracking_number,
        employee_id=t.employee_id,
        employee_name=t.employee.full_name if t.employee else None,
        category_id=t.category_id,
        category_name=t.category.name if t.category else None,
        title=t.title,
        description=t.description,
        status=t.status.value if hasattr(t.status, "value") else str(t.status),
        priority=t.priority.value if hasattr(t.priority, "value") else str(t.priority),
        is_sensitive=t.is_sensitive,
        confidential_assigned_to=t.confidential_assigned_to,
        assigned_agent_name=assigned_name,
        current_tier=active_asg.tier.value if active_asg and hasattr(active_asg.tier, "value") else "TIER_1",
        created_at=t.created_at,
        updated_at=t.updated_at,
        resolved_at=t.resolved_at,
        sla_status=sla_status,
        resolution_due_at=res_due
    )

@router.get("", response_model=List[TicketResponse], summary="List Tickets with RBAC and Filters")
def list_tickets(
    status: Optional[str] = None,
    category_id: Optional[str] = None,
    priority: Optional[str] = None,
    is_sensitive: Optional[bool] = None,
    search: Optional[str] = None,
    limit: int = Query(200, le=1000),
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    """
    List tickets matching filters.
    Applies strict Role-Based Access Control and confidential filtering.
    """
    q = db.query(Ticket)

    # RBAC filtering
    user_role = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if user_role == Role.EMPLOYEE.value:
        # Standard employees can only see tickets they submitted
        q = q.filter(Ticket.employee_id == current_user.emp_id)
    elif user_role == Role.HR_AGENT.value:
        # Regular HR agents cannot see sensitive tickets unless assigned
        q = q.filter(
            (Ticket.is_sensitive == False) | (Ticket.confidential_assigned_to == current_user.emp_id)
        )
    elif user_role == Role.IT_OPERATIONS_PARTNER.value:
        q = q.join(Assignment).filter(
            Ticket.category_id == "CAT-004",
            Assignment.assigned_to_id == current_user.emp_id,
            Assignment.is_active == True,
        )
    # HR_MANAGER, ADMIN, and COMPLIANCE_OFFICER see all tickets

    if status:
        q = q.filter(Ticket.status == status)
    if category_id:
        q = q.filter(Ticket.category_id == category_id)
    if priority:
        q = q.filter(Ticket.priority == priority)
    if is_sensitive is not None:
        q = q.filter(Ticket.is_sensitive == is_sensitive)
    if search:
        term = f"%{search}%"
        q = q.filter(
            (Ticket.title.ilike(term)) |
            (Ticket.tracking_number.ilike(term)) |
            (Ticket.description.ilike(term))
        )

    tickets = q.order_by(Ticket.created_at.desc()).limit(limit).all()
    return [format_ticket_summary(t, db) for t in tickets]

@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED, summary="Submit New HR Request")
def submit_ticket(
    ticket_in: TicketCreate,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    """Submit a new HR ticket. Automatically handles classification, ambiguity check, and SLA initialization."""
    ticket = create_ticket(db, current_user, ticket_in)
    return format_ticket_summary(ticket, db)

@router.get("/{ticket_id}", response_model=TicketDetailResponse, summary="Get Ticket Details")
def get_ticket(
    ticket_id: str,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    """Retrieve full ticket details with conversation thread, SLA status, and assignments."""
    ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if not can_access_ticket(current_user, ticket):
        raise HTTPException(status_code=403, detail="Access denied. This is a confidential request.")

    # Refresh SLA
    refresh_sla_status(db, ticket)

    summary = format_ticket_summary(ticket, db)

    # Filter messages (hide internal notes from standard employees)
    user_role = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    visible_messages = []
    for m in ticket.messages:
        if m.is_internal and user_role == Role.EMPLOYEE.value:
            continue
        visible_messages.append(m)

    return TicketDetailResponse(
        **summary.model_dump(),
        sla=ticket.sla,
        assignments=ticket.assignments,
        messages=visible_messages,
        resolution=ticket.resolution,
        has_active_anomalies=len(ticket.anomalies) > 0,
        anomalies=ticket.anomalies
    )

@router.post("/{ticket_id}/assign", response_model=TicketResponse, summary="Assign or Reassign Ticket")
def assign_ticket_endpoint(
    ticket_id: str,
    request: TicketAssignRequest,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(require_roles(HR_STAFF_ROLES))
):
    """Assign ticket to an HR agent."""
    assign_ticket(
        db=db,
        ticket_id=ticket_id,
        assigned_to_id=request.assigned_to_id,
        assigned_by=current_user,
        tier=request.tier or "TIER_1",
        reason=request.reason
    )
    ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
    return format_ticket_summary(ticket, db)

@router.post("/{ticket_id}/escalate", response_model=TicketResponse, summary="Escalate Ticket")
def escalate_ticket_endpoint(
    ticket_id: str,
    request: TicketEscalateRequest,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(require_roles(HR_STAFF_ROLES))
):
    """Escalate ticket to higher tier or specialist."""
    ticket = escalate_ticket(
        db=db,
        ticket_id=ticket_id,
        actor=current_user,
        request=request
    )
    return format_ticket_summary(ticket, db)

@router.post("/{ticket_id}/resolve", response_model=ResolutionResponse, summary="Resolve Ticket")
def resolve_ticket_endpoint(
    ticket_id: str,
    resolution_in: ResolutionCreate,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(require_roles(TICKET_RESOLVER_ROLES))
):
    """Resolve ticket, cite policy version used, and complete SLA."""
    ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if not can_access_ticket(current_user, ticket):
        raise HTTPException(status_code=403, detail="Access denied for this ticket")
    res = resolve_ticket(
        db=db,
        ticket_id=ticket_id,
        actor=current_user,
        resolution_in=resolution_in
    )
    return res

@router.post("/{ticket_id}/messages", response_model=MessageResponse, summary="Post Message or Note")
def post_message(
    ticket_id: str,
    msg_in: MessageCreate,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    """Add a message or internal note to ticket thread."""
    ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if not can_access_ticket(current_user, ticket):
        raise HTTPException(status_code=403, detail="Access denied for this ticket")
    # Prevent employees from posting internal notes
    user_role = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    is_internal = msg_in.is_internal if user_role in [r.value for r in HR_STAFF_ROLES] else False

    msg = add_message(
        db=db,
        ticket_id=ticket_id,
        sender=current_user,
        content=msg_in.content,
        message_type=msg_in.message_type,
        is_internal=is_internal,
        citations_json=msg_in.citations_json
    )
    return MessageResponse(
        message_id=msg.message_id,
        ticket_id=msg.ticket_id,
        sender_id=msg.sender_id,
        sender_name=current_user.full_name,
        sender_role=user_role,
        content=msg.content,
        message_type=msg.message_type.value if hasattr(msg.message_type, "value") else str(msg.message_type),
        is_internal=msg.is_internal,
        citations_json=msg.citations_json,
        created_at=msg.created_at
    )

@router.post("/{ticket_id}/rate", response_model=ResolutionResponse, summary="Rate Resolution Satisfaction")
def rate_ticket(
    ticket_id: str,
    req: SatisfactionRatingRequest,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    """Submit satisfaction rating and feedback after ticket resolution."""
    ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
    if not ticket or not ticket.resolution:
        raise HTTPException(status_code=404, detail="Resolution record not found")

    if current_user.emp_id != ticket.employee_id:
        raise HTTPException(status_code=403, detail="Only ticket submitter can rate resolution")

    res = ticket.resolution
    res.employee_rating = req.employee_rating
    res.employee_feedback = req.employee_feedback
    db.commit()
    db.refresh(res)
    return res

@router.post("/classify", response_model=ClassificationResult, summary="Test Classification")
def test_classification(payload: dict):
    """Utility endpoint to test AI classification on sample text."""
    title = payload.get("title", "")
    description = payload.get("description", "")
    return classify_text(title, description)

@router.post("/check-ambiguity", response_model=AmbiguityCheckResult, summary="Test Ambiguity")
def test_ambiguity(payload: dict):
    """Utility endpoint to test ambiguity detection on sample text."""
    title = payload.get("title", "")
    description = payload.get("description", "")
    category = payload.get("category_name", "General")
    return detect_ambiguity(title, description, category)

