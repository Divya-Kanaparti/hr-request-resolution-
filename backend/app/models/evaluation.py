"""
Evaluation and Manifest Models
Tracks quantitative evaluation results, metrics, confusion matrices, and dataset checksums.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, Float, DateTime, JSON
from app.database.base import Base

def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    evaluation_id = Column(String(48), primary_key=True, index=True)
    run_timestamp = Column(DateTime, default=utc_now, nullable=False, index=True)
    dataset_profile = Column(String(32), nullable=False)  # starter / full
    seed_used = Column(Integer, default=20261022, nullable=False)
    total_tickets_evaluated = Column(Integer, nullable=False)
    classification_accuracy = Column(Float, nullable=False)
    classification_macro_f1 = Column(Float, nullable=False)
    routing_accuracy = Column(Float, nullable=False)
    sensitive_routing_precision = Column(Float, nullable=False)
    sensitive_routing_recall = Column(Float, nullable=False)
    valid_citation_rate = Column(Float, nullable=False)
    clarification_precision = Column(Float, nullable=False)
    clarification_recall = Column(Float, nullable=False)
    sla_calculation_accuracy = Column(Float, nullable=False)
    anomaly_precision = Column(Float, nullable=False)
    anomaly_recall = Column(Float, nullable=False)
    anomaly_f1 = Column(Float, nullable=False)
    metrics_summary_json = Column(Text, nullable=False)
    confusion_matrix_json = Column(Text, nullable=True)

class DatasetManifest(Base):
    __tablename__ = "dataset_manifests"

    manifest_id = Column(String(48), primary_key=True, index=True)
    profile = Column(String(32), nullable=False, index=True)
    seed = Column(Integer, nullable=False)
    generated_at = Column(DateTime, default=utc_now, nullable=False)
    file_manifest_json = Column(Text, nullable=False)  # Map of file -> row_count, sha256
    overall_checksum = Column(String(64), nullable=False)

