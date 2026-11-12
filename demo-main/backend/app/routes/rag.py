"""
RAG and AI Policy Q&A API Routes
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.rag import RAGQueryRequest, RAGQueryResponse
from app.services.rag_service import generate_rag_answer
from app.core.rbac import get_current_user

router = APIRouter(prefix="/rag", tags=["AI & Policy RAG"])

@router.post("/ask", response_model=RAGQueryResponse, summary="Ask Policy Question (RAG with Citations)")
def ask_policy_rag(
    request: RAGQueryRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Submit a policy question.
    Searches active policy articles and returns an authoritative answer with exact citations.
    """
    audience = "ALL_EMPLOYEES"
    if current_user.role in ["HR_AGENT", "HR_MANAGER", "ADMIN"]:
        audience = "HR_ONLY"

    return generate_rag_answer(
        db=db,
        query=request.query,
        audience=audience,
        department_id=request.department_id,
        category_id=request.category_id,
        top_k=request.top_k or 3
    )

