"""
Database Relational Integrity and Foreign-Key Cascade Test Suite
"""
import pytest
from app.models.employee import Employee, RoleEnum, EmploymentTypeEnum
from app.models.ticket import Ticket, TicketStatusEnum
from app.models.category import PriorityEnum
from app.models.message import Message, MessageTypeEnum
from app.models.assignment import Assignment, TierEnum
from app.models.sla import SLA
from datetime import datetime

def test_ticket_relationships(db):
    emp = db.query(Employee).filter(Employee.emp_id == "EMP-TEST-01").first()
    
    t = Ticket(
        ticket_id="TKT-2026-000001",
        tracking_number="REQ-2026-8801",
        employee_id=emp.emp_id,
        category_id="CAT-001",
        title="Relationship Integrity Check",
        description="Testing complete entity relationships",
        status=TicketStatusEnum.NEW,
        priority=PriorityEnum.MEDIUM,
        is_sensitive=False
    )
    db.add(t)
    db.commit()

    # Add assignment
    asg = Assignment(
        assignment_id="ASG-REL-01",
        ticket_id=t.ticket_id,
        assigned_to_id="EMP-TEST-02",
        assigned_by_id="EMP-TEST-03",
        tier=TierEnum.TIER_1,
        is_active=True
    )
    # Add SLA
    sla = SLA(
        sla_id="SLA-REL-01",
        ticket_id=t.ticket_id,
        priority=PriorityEnum.MEDIUM,
        business_hours_limit=24,
        response_due_at=datetime.utcnow(),
        resolution_due_at=datetime.utcnow()
    )
    # Add message
    msg = Message(
        message_id="MSG-TKT-2026-000001-001",
        ticket_id=t.ticket_id,
        sender_id=emp.emp_id,
        message_type=MessageTypeEnum.EMPLOYEE_NOTE,
        content="Test message relation"
    )
    db.add_all([asg, sla, msg])
    db.commit()

    # Verify relationships
    loaded_ticket = db.query(Ticket).filter(Ticket.ticket_id == "TKT-2026-000001").first()
    assert loaded_ticket.employee.full_name == "Standard Employee"
    assert loaded_ticket.category.name == "Benefits"
    assert len(loaded_ticket.assignments) == 1
    assert loaded_ticket.sla.sla_id == "SLA-REL-01"
    assert len(loaded_ticket.messages) == 1

