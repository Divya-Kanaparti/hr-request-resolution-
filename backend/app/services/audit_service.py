"""
Audit Service
Records immutable audit logs for all system mutations.
"""
from typing import Optional, Any
from sqlalchemy.orm import Session
from app.models.audit import AuditLog
import uuid

def log_audit_event(
    db: Session,
    entity_type: str,
    entity_id: str,
    action: str,
    actor_id: Optional[str] = None,
    details: Optional[Any] = None
) -> AuditLog:
    """Create and persist an immutable audit log entry."""
    audit_id = f"AUD-{uuid.uuid4().hex[:10].upper()}"
    log_entry = AuditLog(
        audit_id=audit_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        actor_id=actor_id,
        details_json=details
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry

