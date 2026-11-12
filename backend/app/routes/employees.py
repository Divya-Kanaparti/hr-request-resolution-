"""
Employees API Routes
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.employee import Employee, RoleEnum, EmploymentTypeEnum, EmployeeStatusEnum
from app.schemas.employee import EmployeeResponse, EmployeeUpdate, EmployeeCreate
from app.core.security import get_password_hash
from app.core.rbac import get_current_user, require_roles, Role, HR_STAFF_ROLES
import uuid

router = APIRouter(prefix="/employees", tags=["Employees"])

@router.get("", response_model=List[EmployeeResponse], summary="List Employees")
def list_employees(
    department_id: Optional[str] = None,
    role: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    current_user: Employee = Depends(require_roles(HR_STAFF_ROLES))
):
    """List employees with optional filtering (HR / Admin only)."""
    q = db.query(Employee)
    if department_id:
        q = q.filter(Employee.department_id == department_id)
    if role:
        q = q.filter(Employee.role == role)
    if search:
        term = f"%{search}%"
        q = q.filter((Employee.full_name.ilike(term)) | (Employee.email.ilike(term)))
    
    employees = q.limit(limit).all()
    res = []
    for emp in employees:
        emp_dict = EmployeeResponse(
            emp_id=emp.emp_id,
            email=emp.email,
            full_name=emp.full_name,
            department_id=emp.department_id,
            role=emp.role.value if hasattr(emp.role, "value") else str(emp.role),
            employment_type=emp.employment_type.value if hasattr(emp.employment_type, "value") else str(emp.employment_type),
            status=emp.status.value if hasattr(emp.status, "value") else str(emp.status),
            is_active=emp.is_active,
            hire_date=emp.hire_date,
            created_at=emp.created_at,
            department_name=emp.department.name if emp.department else None
        )
        res.append(emp_dict)
    return res

@router.get("/{emp_id}", response_model=EmployeeResponse, summary="Get Employee by ID")
def get_employee(
    emp_id: str,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user)
):
    """Retrieve employee details."""
    if current_user.role == Role.EMPLOYEE.value and current_user.emp_id != emp_id:
        raise HTTPException(status_code=403, detail="Access denied")

    emp = db.query(Employee).filter(Employee.emp_id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    return EmployeeResponse(
        emp_id=emp.emp_id,
        email=emp.email,
        full_name=emp.full_name,
        department_id=emp.department_id,
        role=emp.role.value if hasattr(emp.role, "value") else str(emp.role),
        employment_type=emp.employment_type.value if hasattr(emp.employment_type, "value") else str(emp.employment_type),
        status=emp.status.value if hasattr(emp.status, "value") else str(emp.status),
        is_active=emp.is_active,
        hire_date=emp.hire_date,
        created_at=emp.created_at,
        department_name=emp.department.name if emp.department else None
    )

