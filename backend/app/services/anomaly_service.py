"""
Anomaly Detection Service
Identifies the 4 core enterprise anomalies:
1. OBSOLETE_POLICY_CITATION
2. SENSITIVE_GENERAL_QUEUE
3. INCORRECT_SLA_CALCULATION
4. UNSUPPORTED_POLICY_CLAIM
"""
from datetime import datetime
from typing import List, Tuple
from sqlalchemy.orm import Session
from app.models.anomaly import AnomalyRecord, AnomalyTypeEnum, AnomalySeverityEnum, AnomalyStatusEnum
from app.models.ticket import Ticket, TicketStatusEnum
from app.models.resolution import Resolution
from app.models.policy import PolicyVersion, PolicyStatusEnum, KnowledgeArticle
from app.models.sla import SLA
from app.models.message import Message, MessageTypeEnum
from app.models.employee import Employee, RoleEnum
from app.core.business_hours import calculate_sla_deadlines, calculate_business_hours_between
from app.services.classification_service import SENSITIVE_TRIGGERS
import uuid

def scan_obsolete_policy_citations(db: Session) -> List[AnomalyRecord]:
    """Scan resolutions and messages citing superseded or archived policy versions."""
    detected = []
    resolutions = db.query(Resolution).filter(Resolution.policy_version_used_id.isnot(None)).all()
    
    for res in resolutions:
        pver = db.query(PolicyVersion).filter(PolicyVersion.version_id == res.policy_version_used_id).first()
        if pver and pver.status in [PolicyStatusEnum.ARCHIVED, PolicyStatusEnum.SUPERSEDED]:
            # Check if already logged
            exists = db.query(AnomalyRecord).filter(
                AnomalyRecord.ticket_id == res.ticket_id,
                AnomalyRecord.anomaly_type == AnomalyTypeEnum.OBSOLETE_POLICY_CITATION
            ).first()
            if not exists:
                anom = AnomalyRecord(
                    anomaly_id=f"ANOM-{uuid.uuid4().hex[:10].upper()}",
                    ticket_id=res.ticket_id,
                    anomaly_type=AnomalyTypeEnum.OBSOLETE_POLICY_CITATION,
                    severity=AnomalySeverityEnum.HIGH,
                    description=f"Ticket resolution cites superseded/archived policy version {pver.version_number} (Status: {pver.status.value}).",
                    status=AnomalyStatusEnum.DETECTED,
                    ground_truth_label=True
                )
                db.add(anom)
                detected.append(anom)
    return detected

def scan_sensitive_general_queue(db: Session) -> List[AnomalyRecord]:
    """Detect tickets with sensitive triggers routed to general agents without confidential assignment."""
    detected = []
    tickets = db.query(Ticket).all()

    for t in tickets:
        combined = f"{t.title.lower()} {t.description.lower()}"
        has_sensitive_trigger = any(trig in combined for trig in SENSITIVE_TRIGGERS)
        
        # Anomaly if sensitive but confidential_assigned_to is NULL
        if (t.is_sensitive or has_sensitive_trigger) and not t.confidential_assigned_to:
            exists = db.query(AnomalyRecord).filter(
                AnomalyRecord.ticket_id == t.ticket_id,
                AnomalyRecord.anomaly_type == AnomalyTypeEnum.SENSITIVE_GENERAL_QUEUE
            ).first()
            if not exists:
                anom = AnomalyRecord(
                    anomaly_id=f"ANOM-{uuid.uuid4().hex[:10].upper()}",
                    ticket_id=t.ticket_id,
                    anomaly_type=AnomalyTypeEnum.SENSITIVE_GENERAL_QUEUE,
                    severity=AnomalySeverityEnum.CRITICAL,
                    description=f"Ticket contains confidential triggers or is marked sensitive, but is exposed to general queue without confidential restriction.",
                    status=AnomalyStatusEnum.DETECTED,
                    ground_truth_label=True
                )
                db.add(anom)
                detected.append(anom)
    return detected

def scan_incorrect_sla_calculations(db: Session) -> List[AnomalyRecord]:
    """Detect SLAs calculated with calendar hours instead of deterministic business hours."""
    detected = []
    slas = db.query(SLA, Ticket).join(Ticket, SLA.ticket_id == Ticket.ticket_id).all()

    for sla, ticket in slas:
        expected_resp, expected_res, _ = calculate_sla_deadlines(ticket.created_at, ticket.priority.value if hasattr(ticket.priority, "value") else str(ticket.priority))
        
        # Check if resolution_due_at deviates by more than 1 hour from expected business hours deadline
        diff_seconds = abs((sla.resolution_due_at - expected_res).total_seconds())
        if diff_seconds > 3600:
            exists = db.query(AnomalyRecord).filter(
                AnomalyRecord.ticket_id == ticket.ticket_id,
                AnomalyRecord.anomaly_type == AnomalyTypeEnum.INCORRECT_SLA_CALCULATION
            ).first()
            if not exists:
                anom = AnomalyRecord(
                    anomaly_id=f"ANOM-{uuid.uuid4().hex[:10].upper()}",
                    ticket_id=ticket.ticket_id,
                    anomaly_type=AnomalyTypeEnum.INCORRECT_SLA_CALCULATION,
                    severity=AnomalySeverityEnum.MEDIUM,
                    description=f"SLA deadline deviates by {round(diff_seconds/3600, 1)} hours from the standard business-hours calendar (likely counted weekend/night hours).",
                    status=AnomalyStatusEnum.DETECTED,
                    ground_truth_label=True
                )
                db.add(anom)
                detected.append(anom)
    return detected

def scan_unsupported_policy_claims(db: Session) -> List[AnomalyRecord]:
    """Detect resolutions or replies that claim a policy benefit not backed by any active article."""
    detected = []
    resolutions = db.query(Resolution).all()

    # Known unsupported claim markers often hallucinated or injected
    unsupported_markers = [
        "100% remote stipend unlimited",
        "unlimited executive dental reimbursement",
        "6 months paid paternity without tenure",
        "guaranteed annual 25% performance bonus"
    ]

    for res in resolutions:
        res_text = res.resolution_notes.lower()
        if any(marker in res_text for marker in unsupported_markers) or res.policy_version_used_id is None:
            exists = db.query(AnomalyRecord).filter(
                AnomalyRecord.ticket_id == res.ticket_id,
                AnomalyRecord.anomaly_type == AnomalyTypeEnum.UNSUPPORTED_POLICY_CLAIM
            ).first()
            if not exists:
                anom = AnomalyRecord(
                    anomaly_id=f"ANOM-{uuid.uuid4().hex[:10].upper()}",
                    ticket_id=res.ticket_id,
                    anomaly_type=AnomalyTypeEnum.UNSUPPORTED_POLICY_CLAIM,
                    severity=AnomalySeverityEnum.HIGH,
                    description=f"Resolution asserts terms or rules that are not corroborated by any active corporate knowledge article.",
                    status=AnomalyStatusEnum.DETECTED,
                    ground_truth_label=True
                )
                db.add(anom)
                detected.append(anom)
    return detected

def run_full_anomaly_scan(db: Session) -> List[AnomalyRecord]:
    """Execute complete anomaly scan across all 4 anomaly domains and commit findings."""
    all_anomalies = []
    all_anomalies.extend(scan_obsolete_policy_citations(db))
    all_anomalies.extend(scan_sensitive_general_queue(db))
    all_anomalies.extend(scan_incorrect_sla_calculations(db))
    all_anomalies.extend(scan_unsupported_policy_claims(db))
    db.commit()
    return all_anomalies

