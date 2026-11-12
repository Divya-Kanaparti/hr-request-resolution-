"""
Departments API Routes
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.department import Department
from app.schemas.department import DepartmentCreate, DepartmentResponse
from app.core.rbac import get_current_user, require_roles, Role
import uuid

router = APIRouter(prefix="/departments", tags=["Departments"])

@router.get("", response_model=List[DepartmentResponse], summary="List All Departments")
def list_departments(db: Session = Depends(get_db)):
    """Retrieve all corporate departments."""
    return db.query(Department).order_by(Department.name).all()

@router.post("", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED, summary="Create Department")
def create_department(
    dept_in: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles([Role.ADMIN, Role.HR_MANAGER]))
):
    """Create a new corporate department (Admin / HR Manager only)."""
    dept_id = f"DEP-{uuid.uuid4().hex[:6].upper()}"
    dept = Department(
        dept_id=dept_id,
        name=dept_in.name,
        code=dept_in.code.upper(),
        manager_id=dept_in.manager_id,
        location=dept_in.location or "Headquarters"
    )
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept

