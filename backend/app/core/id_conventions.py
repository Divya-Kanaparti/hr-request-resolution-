"""Standard ID generation for tickets, policies, versions, articles, and messages."""
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.message import Message
from app.models.policy import KnowledgeArticle, PolicyDocument, PolicyVersion
from app.models.ticket import Ticket


def _next_id_number(db: Session, column, prefix: str, width: int, maximum: int, offset: int = 0) -> int:
    last_id = db.query(func.max(column)).filter(column.like(f"{prefix}%")).scalar()
    current = 0
    if last_id is not None:
        suffix = last_id[len(prefix):]
        if len(suffix) != width or not suffix.isascii() or not suffix.isdigit():
            raise ValueError(f"Existing ID does not follow the expected format: {last_id}")
        current = int(suffix)

    next_number = current + 1 + offset
    if next_number > maximum:
        raise HTTPException(status_code=409, detail=f"ID sequence exhausted for {prefix}")
    return next_number


def generate_ticket_id(db: Session) -> str:
    year = datetime.utcnow().year
    prefix = f"TKT-{year}-"
    number = _next_id_number(db, Ticket.ticket_id, prefix, 6, 999999)
    return f"{prefix}{number:06d}"


def generate_policy_id(db: Session) -> str:
    year = datetime.utcnow().year
    prefix = f"POL-HR-{year}-"
    number = _next_id_number(db, PolicyDocument.policy_id, prefix, 3, 999)
    return f"{prefix}{number:03d}"


def generate_policy_version_id(db: Session, policy_id: str) -> str:
    prefix = f"VER-{policy_id}-"
    number = _next_id_number(db, PolicyVersion.version_id, prefix, 2, 99)
    return f"{prefix}{number:02d}"


def generate_knowledge_article_id(db: Session, offset: int = 0) -> str:
    prefix = "KB-"
    number = _next_id_number(db, KnowledgeArticle.article_id, prefix, 6, 999999, offset)
    return f"{prefix}{number:06d}"


def generate_message_id(db: Session, ticket_id: str) -> str:
    prefix = f"MSG-{ticket_id}-"
    number = _next_id_number(db, Message.message_id, prefix, 3, 999)
    return f"{prefix}{number:03d}"
