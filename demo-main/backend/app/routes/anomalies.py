"""
Anomaly Detection API Routes
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.anomaly import AnomalyRecord, AnomalyStatusEnum
from app.schemas.anomaly import AnomalyResponse, AnomalyResolveRequest
from app.services.anomaly_service import run_full_anomaly_scan
from app.core.rbac import require_roles, Role, COMPLIANCE_ROLES

router = APIRouter(prefix="/anomalies", tags=["Anomaly Detection"])

@router.get("", response_model=List[AnomalyResponse], summary="List Detected Anomalies")
def list_anomalies(
    anomaly_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(COMPLIANCE_ROLES))
):
    """Retrieve detected enterprise anomalies with ticket context (Admin & Compliance)."""
    q = db.query(AnomalyRecord)
    if anomaly_type:
        q = q.filter(AnomalyRecord.anomaly_type == anomaly_type)
    if status:
        q = q.filter(AnomalyRecord.status == status)

    records = q.order_by(AnomalyRecord.detected_at.desc()).limit(limit).all()
    results = []
    for r in records:
        results.append(AnomalyResponse(
            anomaly_id=r.anomaly_id,
            ticket_id=r.ticket_id,
            anomaly_type=r.anomaly_type.value if hasattr(r.anomaly_type, "value") else str(r.anomaly_type),
            severity=r.severity.value if hasattr(r.severity, "value") else str(r.severity),
            detected_at=r.detected_at,
            description=r.description,
            status=r.status.value if hasattr(r.status, "value") else str(r.status),
            ground_truth_label=r.ground_truth_label,
            ticket_title=r.ticket.title if r.ticket else None,
            ticket_tracking=r.ticket.tracking_number if r.ticket else None
        ))
    return results

@router.post("/scan", response_model=List[AnomalyResponse], summary="Trigger Comprehensive Anomaly Scan")
def trigger_scan(
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(COMPLIANCE_ROLES))
):
    """Run full automated scan across all tickets and records."""
    detected = run_full_anomaly_scan(db)
    return [
        AnomalyResponse(
            anomaly_id=r.anomaly_id,
            ticket_id=r.ticket_id,
            anomaly_type=r.anomaly_type.value if hasattr(r.anomaly_type, "value") else str(r.anomaly_type),
            severity=r.severity.value if hasattr(r.severity, "value") else str(r.severity),
            detected_at=r.detected_at,
            description=r.description,
            status=r.status.value if hasattr(r.status, "value") else str(r.status),
            ground_truth_label=r.ground_truth_label,
            ticket_title=r.ticket.title if r.ticket else None,
            ticket_tracking=r.ticket.tracking_number if r.ticket else None
        ) for r in detected
    ]

@router.put("/{anomaly_id}/resolve", response_model=AnomalyResponse, summary="Resolve Anomaly")
def resolve_anomaly(
    anomaly_id: str,
    req: AnomalyResolveRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(COMPLIANCE_ROLES))
):
    """Mark an anomaly as resolved or false positive."""
    anom = db.query(AnomalyRecord).filter(AnomalyRecord.anomaly_id == anomaly_id).first()
    if not anom:
        raise HTTPException(status_code=404, detail="Anomaly record not found")

    anom.status = AnomalyStatusEnum[req.status] if req.status in AnomalyStatusEnum.__members__ else AnomalyStatusEnum.RESOLVED
    db.commit()
    db.refresh(anom)
    return AnomalyResponse(
        anomaly_id=anom.anomaly_id,
        ticket_id=anom.ticket_id,
        anomaly_type=anom.anomaly_type.value if hasattr(anom.anomaly_type, "value") else str(anom.anomaly_type),
        severity=anom.severity.value if hasattr(anom.severity, "value") else str(anom.severity),
        detected_at=anom.detected_at,
        description=anom.description,
        status=anom.status.value if hasattr(anom.status, "value") else str(anom.status),
        ground_truth_label=anom.ground_truth_label,
        ticket_title=anom.ticket.title if anom.ticket else None,
        ticket_tracking=anom.ticket.tracking_number if anom.ticket else None
    )

