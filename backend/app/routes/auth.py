"""
Authentication API Routes
Supports standard JSON login as well as OAuth2PasswordRequestForm for Swagger UI.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
# from fastapi import APIRouter, Depends, HTTPException, status, Form
# from fastapi.security import OAuth2PasswordRequestForm
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.employee import Employee, RoleEnum, EmploymentTypeEnum
from app.schemas.auth import LoginRequest, TokenResponse, RegisterRequest, UserSummary
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.rbac import get_current_user
from app.services.audit_service import log_audit_event
import uuid
from datetime import date

router = APIRouter(prefix="/auth", tags=["Authentication"])

# @router.post("/login", response_model=TokenResponse, summary="User Login (JSON or Form)")
# def login(
#     login_data: Optional[LoginRequest] = None,
#     form_data: OAuth2PasswordRequestForm = Depends(OAuth2PasswordRequestForm),
#     # form_data: Optional[OAuth2PasswordRequestForm] = Depends(None),
#     username: Optional[str] = Form(None),
#     password: Optional[str] = Form(None),
#     db: Session = Depends(get_db)
# ):
#     """
#     Authenticate user and return JWT access token.
#     Compatible with Swagger Authorize (form-data) and Frontend UI (JSON).
#     """
#     email = None
#     pwd = None

#     if form_data:
#         email = form_data.username
#         pwd = form_data.password
#     elif username and password:
#         email = username
#         pwd = password
#     elif login_data:
#         email = login_data.email
#         pwd = login_data.password

#     if not email or not pwd:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Email and password are required"
#         )

#     user = db.query(Employee).filter(Employee.email == email.strip().lower()).first()
#     if not user or not verify_password(pwd, user.password_hash):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect email or password",
#             headers={"WWW-Authenticate": "Bearer"},
#         )

#     if not user.is_active:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="User account is deactivated"
#         )

#     access_token = create_access_token(data={"sub": user.emp_id, "role": user.role.value if hasattr(user.role, "value") else str(user.role)})

#     user_summary = UserSummary(
#         emp_id=user.emp_id,
#         email=user.email,
#         full_name=user.full_name,
#         department_id=user.department_id,
#         role=user.role.value if hasattr(user.role, "value") else str(user.role),
#         employment_type=user.employment_type.value if hasattr(user.employment_type, "value") else str(user.employment_type),
#         status=user.status.value if hasattr(user.status, "value") else str(user.status)
#     )

#     return TokenResponse(
#         access_token=access_token,
#         token_type="bearer",
#         user=user_summary
#     )


# @router.post("/login", response_model=TokenResponse, summary="User Login (JSON or Form)")
# async def login(
#     request: Request,
#     db: Session = Depends(get_db)
# ):
#     """Authenticate using JSON or form data and return JWT access token."""

#     content_type = request.headers.get("content-type", "").lower()

#     if "application/json" in content_type:
#         data = await request.json()
#         email = data.get("email")
#         pwd = data.get("password")
#     else:
#         form_data = await request.form()
#         email = form_data.get("username") or form_data.get("email")
#         pwd = form_data.get("password")

#     if not email or not pwd:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Email and password are required"
#         )

#     user = db.query(Employee).filter(
#         Employee.email == email.strip().lower()
#     ).first()

#     if not user or not verify_password(pwd, user.password_hash):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect email or password",
#             headers={"WWW-Authenticate": "Bearer"},
#         )

#     if not user.is_active:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="User account is deactivated"
#         )

#     access_token = create_access_token(
#         data={
#             "sub": user.emp_id,
#             "role": user.role.value if hasattr(user.role, "value") else str(user.role)
#         }
#     )

#     user_summary = UserSummary(
#         emp_id=user.emp_id,
#         email=user.email,
#         full_name=user.full_name,
#         department_id=user.department_id,
#         role=user.role.value if hasattr(user.role, "value") else str(user.role),
#         employment_type=user.employment_type.value if hasattr(user.employment_type, "value") else str(user.employment_type),
#         status=user.status.value if hasattr(user.status, "value") else str(user.status)
#     )

#     return TokenResponse(
#         access_token=access_token,
#         token_type="bearer",
#         user=user_summary
#     )


@router.post("/login", response_model=TokenResponse, summary="User Login (JSON)")
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """Authenticate using JSON and return JWT access token."""

    email = login_data.email
    pwd = login_data.password

    if not email or not pwd:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and password are required"
        )

    user = db.query(Employee).filter(
        Employee.email == email.strip().lower()
    ).first()

    if not user or not verify_password(pwd, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )

    access_token = create_access_token(
        data={
            "sub": user.emp_id,
            "role": user.role.value if hasattr(user.role, "value") else str(user.role)
        }
    )

    user_summary = UserSummary(
        emp_id=user.emp_id,
        email=user.email,
        full_name=user.full_name,
        department_id=user.department_id,
        role=user.role.value if hasattr(user.role, "value") else str(user.role),
        employment_type=user.employment_type.value if hasattr(user.employment_type, "value") else str(user.employment_type),
        status=user.status.value if hasattr(user.status, "value") else str(user.status)
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_summary
    )

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED, summary="Register New Employee")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new employee into the system."""
    existing = db.query(Employee).filter(Employee.email == req.email.strip().lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An employee with this email already exists"
        )

    emp_id = f"EMP-{uuid.uuid4().hex[:6].upper()}"
    new_user = Employee(
        emp_id=emp_id,
        email=req.email.strip().lower(),
        password_hash=get_password_hash(req.password),
        full_name=req.full_name,
        department_id=req.department_id,
        role=RoleEnum[req.role] if req.role in RoleEnum.__members__ else RoleEnum.EMPLOYEE,
        employment_type=EmploymentTypeEnum[req.employment_type] if req.employment_type in EmploymentTypeEnum.__members__ else EmploymentTypeEnum.FULL_TIME,
        hire_date=date.today(),
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    log_audit_event(
        db=db,
        entity_type="EMPLOYEE",
        entity_id=new_user.emp_id,
        action="REGISTER_EMPLOYEE",
        actor_id=new_user.emp_id,
        details={"email": new_user.email, "role": new_user.role.value}
    )

    access_token = create_access_token(data={"sub": new_user.emp_id, "role": new_user.role.value})
    user_summary = UserSummary(
        emp_id=new_user.emp_id,
        email=new_user.email,
        full_name=new_user.full_name,
        department_id=new_user.department_id,
        role=new_user.role.value,
        employment_type=new_user.employment_type.value,
        status=new_user.status.value
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_summary
    )

@router.get("/me", response_model=UserSummary, summary="Get Current Authenticated User")
def get_me(current_user: Employee = Depends(get_current_user)):
    """Retrieve identity and permissions of the calling user."""
    return UserSummary(
        emp_id=current_user.emp_id,
        email=current_user.email,
        full_name=current_user.full_name,
        department_id=current_user.department_id,
        role=current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role),
        employment_type=current_user.employment_type.value if hasattr(current_user.employment_type, "value") else str(current_user.employment_type),
        status=current_user.status.value if hasattr(current_user.status, "value") else str(current_user.status)
    )

