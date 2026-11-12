"""
Ticket Participant Model
Records users collaborating or involved in a ticket.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from app.database.base import Base

def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class ParticipantRoleEnum(str, enum.Enum):
    REQUESTER = "REQUESTER"
    PRIMARY_AGENT = "PRIMARY_AGENT"
    COLLABORATOR = "COLLABORATOR"
    SUPERVISOR = "SUPERVISOR"
    COMPLIANCE_REVIEWER = "COMPLIANCE_REVIEWER"

class TicketParticipant(Base):
    __tablename__ = "ticket_participants"

    participant_id = Column(String(48), primary_key=True, index=True)
    ticket_id = Column(String(32), ForeignKey("tickets.ticket_id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id = Column(String(32), ForeignKey("employees.emp_id", ondelete="CASCADE"), nullable=False, index=True)
    role_in_ticket = Column(SQLEnum(ParticipantRoleEnum, native_enum=False), nullable=False, default=ParticipantRoleEnum.COLLABORATOR)
    joined_at = Column(DateTime, default=utc_now, nullable=False)

    ticket = relationship("Ticket", back_populates="participants")
    employee = relationship("Employee")

