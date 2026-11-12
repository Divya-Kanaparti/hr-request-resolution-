"""
Policies API Routes
Version-controlled policy documents and knowledge articles.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.policy import PolicyDocument, PolicyVersion, KnowledgeArticle, PolicyStatusEnum
from app.schemas.policy import (
    PolicyDocumentResponse, PolicyDocumentCreate,
    PolicyVersionResponse, PolicyVersionCreate,
    KnowledgeArticleResponse, KnowledgeArticleCreate
)
from app.core.rbac import get_current_user, require_roles, Role
from app.services.policy_service import create_policy_document, create_new_version

router = APIRouter(prefix="/policies", tags=["Policies"])

@router.get("", response_model=List[PolicyDocumentResponse], summary="List All Policies")
def list_policies(
    category_id: Optional[str] = None,
    audience: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Retrieve all corporate policies with version metadata."""
    q = db.query(PolicyDocument)
    if category_id:
        q = q.filter(PolicyDocument.category_id == category_id)
    if audience:
        q = q.filter(PolicyDocument.audience == audience)

    policies = q.all()
    results = []
    for p in policies:
        versions_res = []
        for v in p.versions:
            articles_res = [
                KnowledgeArticleResponse(
                    article_id=a.article_id,
                    policy_version_id=a.policy_version_id,
                    title=a.title,
                    section_number=a.section_number,
                    content=a.content,
                    keywords=a.keywords,
                    audience=a.audience.value if hasattr(a.audience, "value") else str(a.audience),
                    is_published=a.is_published,
                    created_at=a.created_at
                ) for a in v.articles
            ]
            versions_res.append(
                PolicyVersionResponse(
                    version_id=v.version_id,
                    policy_id=v.policy_id,
                    version_number=v.version_number,
                    status=v.status.value if hasattr(v.status, "value") else str(v.status),
                    effective_from=v.effective_from,
                    effective_to=v.effective_to,
                    summary=v.summary,
                    content=v.content,
                    changelog=v.changelog,
                    approved_by=v.approved_by,
                    approved_at=v.approved_at,
                    created_at=v.created_at,
                    articles=articles_res
                )
            )

        results.append(
            PolicyDocumentResponse(
                policy_id=p.policy_id,
                doc_code=p.doc_code,
                title=p.title,
                category_id=p.category_id,
                department_id=p.department_id,
                audience=p.audience.value if hasattr(p.audience, "value") else str(p.audience),
                owner_id=p.owner_id,
                created_at=p.created_at,
                category_name=p.category.name if p.category else None,
                department_name=p.department.name if p.department else None,
                versions=versions_res
            )
        )
    return results

@router.get("/{policy_id}", response_model=PolicyDocumentResponse, summary="Get Policy Document")
def get_policy(policy_id: str, db: Session = Depends(get_db)):
    """Retrieve a single policy document by ID."""
    p = db.query(PolicyDocument).filter(PolicyDocument.policy_id == policy_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Policy not found")

    versions_res = []
    for v in p.versions:
        articles_res = [
            KnowledgeArticleResponse(
                article_id=a.article_id,
                policy_version_id=a.policy_version_id,
                title=a.title,
                section_number=a.section_number,
                content=a.content,
                keywords=a.keywords,
                audience=a.audience.value if hasattr(a.audience, "value") else str(a.audience),
                is_published=a.is_published,
                created_at=a.created_at
            ) for a in v.articles
        ]
        versions_res.append(
            PolicyVersionResponse(
                version_id=v.version_id,
                policy_id=v.policy_id,
                version_number=v.version_number,
                status=v.status.value if hasattr(v.status, "value") else str(v.status),
                effective_from=v.effective_from,
                effective_to=v.effective_to,
                summary=v.summary,
                content=v.content,
                changelog=v.changelog,
                approved_by=v.approved_by,
                approved_at=v.approved_at,
                created_at=v.created_at,
                articles=articles_res
            )
        )

    return PolicyDocumentResponse(
        policy_id=p.policy_id,
        doc_code=p.doc_code,
        title=p.title,
        category_id=p.category_id,
        department_id=p.department_id,
        audience=p.audience.value if hasattr(p.audience, "value") else str(p.audience),
        owner_id=p.owner_id,
        created_at=p.created_at,
        category_name=p.category.name if p.category else None,
        department_name=p.department.name if p.department else None,
        versions=versions_res
    )

@router.post("", response_model=PolicyDocumentResponse, status_code=status.HTTP_201_CREATED, summary="Create Policy Document")
def create_policy(
    doc_in: PolicyDocumentCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles([Role.ADMIN, Role.HR_MANAGER, Role.COMPLIANCE_OFFICER]))
):
    """Author a new policy document (Admin, HR Manager, Compliance Officer only)."""
    pdoc = create_policy_document(db, current_user, doc_in)
    return get_policy(pdoc.policy_id, db)

@router.post("/{policy_id}/versions", response_model=PolicyVersionResponse, status_code=status.HTTP_201_CREATED, summary="Create New Policy Version")
def create_version_endpoint(
    policy_id: str,
    v_in: PolicyVersionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles([Role.ADMIN, Role.HR_MANAGER, Role.COMPLIANCE_OFFICER]))
):
    """Publish a new version for an existing policy, archiving/superseding older versions."""
    pver = create_new_version(db, policy_id, current_user, v_in)
    return PolicyVersionResponse(
        version_id=pver.version_id,
        policy_id=pver.policy_id,
        version_number=pver.version_number,
        status=pver.status.value if hasattr(pver.status, "value") else str(pver.status),
        effective_from=pver.effective_from,
        effective_to=pver.effective_to,
        summary=pver.summary,
        content=pver.content,
        changelog=pver.changelog,
        approved_by=pver.approved_by,
        approved_at=pver.approved_at,
        created_at=pver.created_at,
        articles=[
            KnowledgeArticleResponse(
                article_id=a.article_id,
                policy_version_id=a.policy_version_id,
                title=a.title,
                section_number=a.section_number,
                content=a.content,
                keywords=a.keywords,
                audience=a.audience.value if hasattr(a.audience, "value") else str(a.audience),
                is_published=a.is_published,
                created_at=a.created_at
            ) for a in pver.articles
        ]
    )

