"""
Categories API Routes
"""
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.category import Category, PriorityEnum, TierEnum
from app.schemas.category import CategoryCreate, CategoryResponse
from app.core.rbac import require_roles, Role
import uuid

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.get("", response_model=List[CategoryResponse], summary="List All Ticket Categories")
def list_categories(db: Session = Depends(get_db)):
    """Retrieve all operational ticket categories."""
    return db.query(Category).order_by(Category.name).all()

@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED, summary="Create Category")
def create_category(
    cat_in: CategoryCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles([Role.ADMIN, Role.HR_MANAGER]))
):
    """Add a new ticket category."""
    cat_id = f"CAT-{uuid.uuid4().hex[:6].upper()}"
    cat = Category(
        category_id=cat_id,
        name=cat_in.name,
        code=cat_in.code.upper(),
        description=cat_in.description,
        default_priority=PriorityEnum[cat_in.default_priority],
        is_sensitive_default=cat_in.is_sensitive_default,
        tier=TierEnum[cat_in.tier]
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat

