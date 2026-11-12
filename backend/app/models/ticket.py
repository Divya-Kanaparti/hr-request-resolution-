"""
Ticket Model
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from app.database.base import Base
from app.models.category import PriorityEnum

class TicketStatusEnum(str, enum.Enum):
    NEW = "NEW"
    CLARIFICATION_NEEDED = "CLARIFICATION_NEEDED"
    IN_PROGRESS = "IN_PROGRESS"
    ESCALATED = "ESCALATED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"

class Ticket(Base):
    __tablename__ = "tickets"

    ticket_id = Column(String(32), primary_key=True, index=True)
    tracking_number = Column(String(48), unique=True, nullable=False, index=True)
    employee_id = Column(String(32), ForeignKey("employees.emp_id", ondelete="RESTRICT"), nullable=False, index=True)
    category_id = Column(String(32), ForeignKey("categories.category_id", ondelete="RESTRICT"), nullable=False, index=True)
    title = Column(String(220), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(SQLEnum(TicketStatusEnum), nullable=False, default=TicketStatusEnum.NEW, index=True)
    priority = Column(SQLEnum(PriorityEnum), nullable=False, default=PriorityEnum.MEDIUM, index=True)
    is_sensitive = Column(Boolean, nullable=False, default=False, index=True)
    confidential_assigned_to = Column(String(32), ForeignKey("employees.emp_id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    employee = relationship("Employee", back_populates="submitted_tickets", foreign_keys=[employee_id])
    category = relationship("Category", back_populates="tickets")
    confidential_agent = relationship("Employee", back_populates="confidential_tickets", foreign_keys=[confidential_assigned_to])
    assignments = relationship("Assignment", back_populates="ticket", cascade="all, delete-orphan", order_by="desc(Assignment.assigned_at)")
    sla = relationship("SLA", back_populates="ticket", uselist=False, cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="ticket", cascade="all, delete-orphan", order_by="Message.created_at")
    resolution = relationship("Resolution", back_populates="ticket", uselist=False, cascade="all, delete-orphan")
    anomalies = relationship("AnomalyRecord", back_populates="ticket", cascade="all, delete-orphan")

