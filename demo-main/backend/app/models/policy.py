"""
Policy Document, Policy Version, and Knowledge Article Models
"""
from datetime import datetime, date
from sqlalchemy import Column, String, Text, Date, Boolean, DateTime, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
import enum
from app.database.base import Base

class AudienceEnum(str, enum.Enum):
    ALL_EMPLOYEES = "ALL_EMPLOYEES"
    MANAGERS_ONLY = "MANAGERS_ONLY"
    FULL_TIME_ONLY = "FULL_TIME_ONLY"
    CONTRACTORS = "CONTRACTORS"
    HR_ONLY = "HR_ONLY"

class PolicyStatusEnum(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    SUPERSEDED = "SUPERSEDED"

class PolicyDocument(Base):
    __tablename__ = "policy_documents"

    policy_id = Column(String(32), primary_key=True, index=True)
    doc_code = Column(String(40), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    category_id = Column(String(32), ForeignKey("categories.category_id", ondelete="RESTRICT"), nullable=False, index=True)
    department_id = Column(String(32), ForeignKey("departments.dept_id", ondelete="RESTRICT"), nullable=False)
    audience = Column(SQLEnum(AudienceEnum), nullable=False, default=AudienceEnum.ALL_EMPLOYEES)
    owner_id = Column(String(32), ForeignKey("employees.emp_id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    category = relationship("Category", back_populates="policies")
    department = relationship("Department", back_populates="policies")
    owner = relationship("Employee", back_populates="policies_owned", foreign_keys=[owner_id])
    versions = relationship("PolicyVersion", back_populates="policy", cascade="all, delete-orphan", order_by="desc(PolicyVersion.version_number)")

class PolicyVersion(Base):
    __tablename__ = "policy_versions"

    version_id = Column(String(32), primary_key=True, index=True)
    policy_id = Column(String(32), ForeignKey("policy_documents.policy_id", ondelete="CASCADE"), nullable=False)
    version_number = Column(String(16), nullable=False)
    status = Column(SQLEnum(PolicyStatusEnum), nullable=False, default=PolicyStatusEnum.DRAFT, index=True)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    summary = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    changelog = Column(Text, nullable=True)
    approved_by = Column(String(32), ForeignKey("employees.emp_id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("policy_id", "version_number", name="uk_policy_version"),
    )

    # Relationships
    policy = relationship("PolicyDocument", back_populates="versions")
    approver = relationship("Employee", foreign_keys=[approved_by])
    articles = relationship("KnowledgeArticle", back_populates="policy_version", cascade="all, delete-orphan")
    resolutions = relationship("Resolution", back_populates="policy_version_used")

class KnowledgeArticle(Base):
    __tablename__ = "knowledge_articles"

    article_id = Column(String(32), primary_key=True, index=True)
    policy_version_id = Column(String(32), ForeignKey("policy_versions.version_id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(220), nullable=False)
    section_number = Column(String(32), nullable=False, index=True)
    content = Column(Text, nullable=False)
    keywords = Column(String(500), nullable=True)
    audience = Column(SQLEnum(AudienceEnum), nullable=False, default=AudienceEnum.ALL_EMPLOYEES)
    is_published = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    policy_version = relationship("PolicyVersion", back_populates="articles")

