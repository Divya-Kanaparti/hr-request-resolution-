"""
Department Model
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import Base

class Department(Base):
    __tablename__ = "departments"

    dept_id = Column(String(32), primary_key=True, index=True)
    name = Column(String(120), nullable=False, unique=True)
    code = Column(String(32), nullable=False, unique=True, index=True)
    manager_id = Column(String(32), ForeignKey("employees.emp_id", ondelete="SET NULL", use_alter=True, name="fk_dept_manager"), nullable=True)
    location = Column(String(120), nullable=False, default="Headquarters")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    employees = relationship("Employee", back_populates="department", foreign_keys="Employee.department_id")
    policies = relationship("PolicyDocument", back_populates="department")

