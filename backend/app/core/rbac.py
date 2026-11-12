"""
Role-Based Access Control (RBAC) and Auth Dependencies
"""
from enum import Enum
from typing import List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.security import decode_access_token
from app.database.session import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)
http_bearer = HTTPBearer(auto_error=False)

class Role(str, Enum):
    EMPLOYEE = "EMPLOYEE"
    HR_AGENT = "HR_AGENT"
    HR_MANAGER = "HR_MANAGER"
    ADMIN = "ADMIN"
    COMPLIANCE_OFFICER = "COMPLIANCE_OFFICER"

HR_STAFF_ROLES = [Role.HR_AGENT, Role.HR_MANAGER, Role.ADMIN, Role.COMPLIANCE_OFFICER]
MANAGEMENT_ROLES = [Role.HR_MANAGER, Role.ADMIN]
COMPLIANCE_ROLES = [Role.COMPLIANCE_OFFICER, Role.ADMIN]

def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    bearer_creds: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
    db: Session = Depends(get_db)
):
    """Retrieve and validate current authenticated user from token."""
    raw_token = token
    if not raw_token and bearer_creds:
        raw_token = bearer_creds.credentials

    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(raw_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    emp_id = payload.get("sub")
    if not emp_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token subject invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )

    from app.models.employee import Employee
    user = db.query(Employee).filter(Employee.emp_id == emp_id, Employee.is_active == True).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

def require_roles(allowed_roles: List[Role]):
    """Dependency factory checking that the authenticated user has an allowed role."""
    def role_checker(current_user = Depends(get_current_user)):
        if current_user.role not in [r.value for r in allowed_roles] and current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required roles: {[r.value if isinstance(r, Role) else r for r in allowed_roles]}"
            )
        return current_user
    return role_checker

def can_access_ticket(user, ticket) -> bool:
    """
    Enforce confidential routing and sensitive-ticket privacy:
    - Ticket owner (employee) can see their own ticket.
    - If ticket is NOT sensitive, any HR staff can see it.
    - If ticket IS sensitive:
      * Ticket owner can see it.
      * Assigned confidential HR personnel can see it.
      * Compliance Officer and Admin can see it.
      * HR Manager can see it.
      * Regular HR Agent CANNOT see it unless specifically assigned.
    """
    if user.emp_id == ticket.employee_id:
        return True
    if user.role in [Role.ADMIN.value, Role.COMPLIANCE_OFFICER.value, Role.HR_MANAGER.value]:
        return True
    if not ticket.is_sensitive:
        return user.role in [Role.HR_AGENT.value, Role.HR_MANAGER.value, Role.ADMIN.value, Role.COMPLIANCE_OFFICER.value]
    # For sensitive ticket, regular HR agent must be the assigned confidential agent
    if ticket.confidential_assigned_to == user.emp_id:
        return True
    return False

