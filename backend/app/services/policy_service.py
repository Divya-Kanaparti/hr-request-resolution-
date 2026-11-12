"""
Policy and Knowledge Management Service
"""
from datetime import date, datetime
from typing import Optional, List
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.policy import PolicyDocument, PolicyVersion, KnowledgeArticle, PolicyStatusEnum
from app.models.employee import Employee
from app.schemas.policy import PolicyDocumentCreate, PolicyVersionCreate, KnowledgeArticleCreate
from app.services.audit_service import log_audit_event
from app.core.id_conventions import (
    generate_knowledge_article_id,
    generate_policy_id,
    generate_policy_version_id,
)

def create_policy_document(
    db: Session,
    creator: Employee,
    doc_in: PolicyDocumentCreate
) -> PolicyDocument:
    """Create a new policy document with its initial draft/active version."""
    policy_id = generate_policy_id(db)
    pdoc = PolicyDocument(
        policy_id=policy_id,
        doc_code=doc_in.doc_code,
        title=doc_in.title,
        category_id=doc_in.category_id,
        department_id=doc_in.department_id,
        audience=doc_in.audience,
        owner_id=creator.emp_id
    )
    db.add(pdoc)
    db.flush()

    if doc_in.initial_version:
        v_in = doc_in.initial_version
        version_id = generate_policy_version_id(db, pdoc.policy_id)
        pver = PolicyVersion(
            version_id=version_id,
            policy_id=pdoc.policy_id,
            version_number=v_in.version_number,
            status=PolicyStatusEnum[v_in.status],
            effective_from=v_in.effective_from,
            effective_to=v_in.effective_to,
            summary=v_in.summary,
            content=v_in.content,
            changelog=v_in.changelog or "Initial release",
            approved_by=creator.emp_id,
            approved_at=datetime.utcnow()
        )
        db.add(pver)
        db.flush()

        if v_in.articles:
            for article_index, art_in in enumerate(v_in.articles):
                art = KnowledgeArticle(
                    article_id=generate_knowledge_article_id(db, article_index),
                    policy_version_id=pver.version_id,
                    title=art_in.title,
                    section_number=art_in.section_number,
                    content=art_in.content,
                    keywords=art_in.keywords,
                    audience=art_in.audience,
                    is_published=art_in.is_published
                )
                db.add(art)

    db.commit()
    db.refresh(pdoc)
    log_audit_event(
        db=db,
        entity_type="POLICY",
        entity_id=pdoc.policy_id,
        action="CREATE_POLICY",
        actor_id=creator.emp_id,
        details={"doc_code": pdoc.doc_code, "title": pdoc.title}
    )
    return pdoc

def create_new_version(
    db: Session,
    policy_id: str,
    creator: Employee,
    v_in: PolicyVersionCreate
) -> PolicyVersion:
    """Create a new version of an existing policy document and supersede previous active versions."""
    pdoc = db.query(PolicyDocument).filter(PolicyDocument.policy_id == policy_id).first()
    if not pdoc:
        raise HTTPException(status_code=404, detail="Policy document not found")

    # If new version is marked ACTIVE, supersede current active version
    if v_in.status == "ACTIVE":
        active_versions = db.query(PolicyVersion).filter(
            PolicyVersion.policy_id == policy_id,
            PolicyVersion.status == PolicyStatusEnum.ACTIVE
        ).all()
        for old_ver in active_versions:
            old_ver.status = PolicyStatusEnum.SUPERSEDED
            if not old_ver.effective_to:
                old_ver.effective_to = v_in.effective_from

    version_id = generate_policy_version_id(db, pdoc.policy_id)
    pver = PolicyVersion(
        version_id=version_id,
        policy_id=pdoc.policy_id,
        version_number=v_in.version_number,
        status=PolicyStatusEnum[v_in.status],
        effective_from=v_in.effective_from,
        effective_to=v_in.effective_to,
        summary=v_in.summary,
        content=v_in.content,
        changelog=v_in.changelog,
        approved_by=creator.emp_id,
        approved_at=datetime.utcnow()
    )
    db.add(pver)
    db.flush()

    if v_in.articles:
        for article_index, art_in in enumerate(v_in.articles):
            art = KnowledgeArticle(
                article_id=generate_knowledge_article_id(db, article_index),
                policy_version_id=pver.version_id,
                title=art_in.title,
                section_number=art_in.section_number,
                content=art_in.content,
                keywords=art_in.keywords,
                audience=art_in.audience,
                is_published=art_in.is_published
            )
            db.add(art)

    db.commit()
    db.refresh(pver)

    log_audit_event(
        db=db,
        entity_type="POLICY_VERSION",
        entity_id=pver.version_id,
        action="CREATE_VERSION",
        actor_id=creator.emp_id,
        details={"version_number": pver.version_number, "status": pver.status.value}
    )
    return pver

