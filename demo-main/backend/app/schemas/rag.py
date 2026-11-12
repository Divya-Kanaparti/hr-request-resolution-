"""
RAG and Question Answering Schemas
"""
from typing import List, Optional
from pydantic import BaseModel

class CitationItem(BaseModel):
    policy_doc_code: str
    policy_title: str
    version_number: str
    section_number: str
    article_title: str
    quote: str
    relevance_score: float

class RAGQueryRequest(BaseModel):
    query: str
    employee_audience: Optional[str] = "ALL_EMPLOYEES"
    department_id: Optional[str] = None
    category_id: Optional[str] = None
    top_k: Optional[int] = 3

class RAGQueryResponse(BaseModel):
    query: str
    answer: str
    citations: List[CitationItem] = []
    is_ambiguous: bool = False
    clarification_question: Optional[str] = None
    confidence_score: float
    model_used: str

