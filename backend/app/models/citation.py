"""
Policy Citation Model
Stores verbatim policy and knowledge article evidence for ticket answers.
"""
from datetime import datetime, timezone, date
from sqlalchemy import Column, String, Text, Date, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.database.base import Base

def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class PolicyCitation(Base):
    __tablename__ = "policy_citations"

    citation_id = Column(String(48), primary_key=True, index=True)
    ticket_id = Column(String(32), ForeignKey("tickets.ticket_id", ondelete="CASCADE"), nullable=False, index=True)
    message_id = Column(String(48), ForeignKey("messages.message_id", ondelete="SET NULL"), nullable=True, index=True)
    resolution_id = Column(String(48), ForeignKey("resolutions.resolution_id", ondelete="SET NULL"), nullable=True, index=True)
    policy_id = Column(String(48), ForeignKey("policy_documents.policy_id", ondelete="CASCADE"), nullable=False, index=True)
    policy_version_id = Column(String(48), ForeignKey("policy_versions.version_id", ondelete="CASCADE"), nullable=False, index=True)
    article_id = Column(String(48), ForeignKey("knowledge_articles.article_id", ondelete="SET NULL"), nullable=True, index=True)
    passage_identifier = Column(String(64), nullable=True)  # e.g. "Sec 2.1"
    exact_passage = Column(Text, nullable=False)
    policy_effective_date = Column(Date, nullable=False)
    decision_timestamp = Column(DateTime, default=utc_now, nullable=False)
    confidence_score = Column(Float, default=1.0)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    # Relationships
    ticket = relationship("Ticket", back_populates="citations")
    policy = relationship("PolicyDocument")
    policy_version = relationship("PolicyVersion")
    article = relationship("KnowledgeArticle")

