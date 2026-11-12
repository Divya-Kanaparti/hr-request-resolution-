"""
SLA API Routes
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.sla import SLACheckResult
from app.services.sla_service import scan_all_active_slas
from app.core.rbac import require_roles, Role, HR_STAFF_ROLES

router = APIRouter(prefix="/sla", tags=["SLA Monitoring"])

@router.post("/check-breaches", response_model=SLACheckResult, summary="Batch Scan SLA Breaches")
def check_sla_breaches(
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(HR_STAFF_ROLES))
):
    """Scan all open tickets and flag SLA breaches."""
    checked, breached, updated_ids = scan_all_active_slas(db)
    return SLACheckResult(
        checked_count=checked,
        breached_count=breached,
        updated_tickets=updated_ids
    )

