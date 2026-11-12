"""
Employee Model
"""
from datetime import datetime, date
from sqlalchemy import Column, String, Date, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from app.database.base import Base

class RoleEnum(str, enum.Enum):
    EMPLOYEE = "EMPLOYEE"
    HR_AGENT = "HR_AGENT"
    HR_MANAGER = "HR_MANAGER"
    ADMIN = "ADMIN"
    COMPLIANCE_OFFICER = "COMPLIANCE_OFFICER"
    IT_OPERATIONS_PARTNER = "IT_OPERATIONS_PARTNER"

class EmploymentTypeEnum(str, enum.Enum):
    FULL_TIME = "FULL_TIME"
    PART_TIME = "PART_TIME"
    CONTRACT = "CONTRACT"
    INTERN = "INTERN"

class EmployeeStatusEnum(str, enum.Enum):
    ACTIVE = "ACTIVE"
    ON_LEAVE = "ON_LEAVE"
    SUSPENDED = "SUSPENDED"
    TERMINATED = "TERMINATED"

class Employee(Base):
    __tablename__ = "employees"

    emp_id = Column(String(32), primary_key=True, index=True)
    email = Column(String(160), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(120), nullable=False)
    department_id = Column(String(32), ForeignKey("departments.dept_id", ondelete="RESTRICT"), nullable=False, index=True)
    role = Column(SQLEnum(RoleEnum), nullable=False, default=RoleEnum.EMPLOYEE, index=True)
    employment_type = Column(SQLEnum(EmploymentTypeEnum), nullable=False, default=EmploymentTypeEnum.FULL_TIME)
    hire_date = Column(Date, nullable=False, default=date.today)
    status = Column(SQLEnum(EmployeeStatusEnum), nullable=False, default=EmployeeStatusEnum.ACTIVE)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    department = relationship("Department", back_populates="employees", foreign_keys=[department_id])
    submitted_tickets = relationship("Ticket", back_populates="employee", foreign_keys="Ticket.employee_id")
    confidential_tickets = relationship("Ticket", back_populates="confidential_agent", foreign_keys="Ticket.confidential_assigned_to")
    assignments_received = relationship("Assignment", back_populates="assigned_to", foreign_keys="Assignment.assigned_to_id")
    assignments_created = relationship("Assignment", back_populates="assigned_by", foreign_keys="Assignment.assigned_by_id")
    messages = relationship("Message", back_populates="sender", foreign_keys="Message.sender_id")
    resolutions = relationship("Resolution", back_populates="resolver", foreign_keys="Resolution.resolved_by_id")
    policies_owned = relationship("PolicyDocument", back_populates="owner", foreign_keys="PolicyDocument.owner_id")

