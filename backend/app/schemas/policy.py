"""
Policy Schemas
"""
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel

class KnowledgeArticleBase(BaseModel):
    title: str
    section_number: str
    content: str
    keywords: Optional[str] = None
    audience: str = "ALL_EMPLOYEES"
    is_published: bool = True

class KnowledgeArticleCreate(KnowledgeArticleBase):
    pass

class KnowledgeArticleResponse(KnowledgeArticleBase):
    article_id: str
    policy_version_id: str
    created_at: datetime

    class Config:
        from_attributes = True

class PolicyVersionBase(BaseModel):
    version_number: str
    status: str = "ACTIVE"
    effective_from: date
    effective_to: Optional[date] = None
    summary: str
    content: str
    changelog: Optional[str] = None

class PolicyVersionCreate(PolicyVersionBase):
    articles: Optional[List[KnowledgeArticleCreate]] = None

class PolicyVersionResponse(PolicyVersionBase):
    version_id: str
    policy_id: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    articles: Optional[List[KnowledgeArticleResponse]] = []

    class Config:
        from_attributes = True

class PolicyDocumentBase(BaseModel):
    doc_code: str
    title: str
    category_id: str
    department_id: str
    audience: str = "ALL_EMPLOYEES"

class PolicyDocumentCreate(PolicyDocumentBase):
    initial_version: Optional[PolicyVersionCreate] = None

class PolicyDocumentResponse(PolicyDocumentBase):
    policy_id: str
    owner_id: str
    created_at: datetime
    category_name: Optional[str] = None
    department_name: Optional[str] = None
    versions: Optional[List[PolicyVersionResponse]] = []

    class Config:
        from_attributes = True

