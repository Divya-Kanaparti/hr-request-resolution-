"""
Audit Log API Routes
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.audit import AuditLog
from app.schemas.audit import AuditLogResponse
from app.core.rbac import require_roles, Role, COMPLIANCE_ROLES

router = APIRouter(prefix="/audit", tags=["Audit Logs"])

@router.get("", response_model=List[AuditLogResponse], summary="List Immutable Audit Logs")
def list_audit_logs(
    entity_type: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(COMPLIANCE_ROLES))
):
    """Retrieve immutable audit events history (Admin and Compliance Officer only)."""
    q = db.query(AuditLog)
    if entity_type:
        q = q.filter(AuditLog.entity_type == entity_type)
    if action:
        q = q.filter(AuditLog.action == action)

    logs = q.order_by(AuditLog.created_at.desc()).limit(limit).all()
    results = []
    for l in logs:
        results.append(AuditLogResponse(
            audit_id=l.audit_id,
            entity_type=l.entity_type,
            entity_id=l.entity_id,
            action=l.action,
            actor_id=l.actor_id,
            actor_name=l.actor.full_name if l.actor else "System",
            details_json=l.details_json,
            created_at=l.created_at
        ))
    return results

