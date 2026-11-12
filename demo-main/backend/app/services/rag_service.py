"""
RAG and Policy Question-Answering Service
Combines vector embeddings, Gemini LLM (configurable), and exact citation retrieval.
"""
from datetime import date, datetime
from typing import List, Dict, Any, Optional
import math
import re
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.policy import PolicyDocument, PolicyVersion, KnowledgeArticle, PolicyStatusEnum
from app.schemas.rag import RAGQueryResponse, CitationItem

# Optional imports for Gemini and Embeddings
try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False

# try:
#     import chromadb
#     HAS_CHROMA = True
# except ImportError:
#     HAS_CHROMA = False
# ChromaDB disabled because its native gRPC dependency
# is blocked by Windows security. The policy search
# service uses its SQLAlchemy fallback.
HAS_CHROMA = False
_embedding_model = None

def get_embedding_model():
    """Lazy load SentenceTransformer model if installed."""
    global _embedding_model
    if _embedding_model is None and HAS_SENTENCE_TRANSFORMERS:
        try:
            _embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        except Exception:
            _embedding_model = None
    return _embedding_model

def simple_token_similarity(query: str, text: str) -> float:
    """Calculate token overlap / BM25-like similarity for robust zero-dependency matching."""
    q_tokens = set(re.findall(r'\w+', query.lower()))
    t_tokens = set(re.findall(r'\w+', text.lower()))
    if not q_tokens or not t_tokens:
        return 0.0
    intersection = q_tokens.intersection(t_tokens)
    return len(intersection) / (math.sqrt(len(q_tokens)) * math.sqrt(len(t_tokens)))

def search_knowledge_base(
    db: Session,
    query: str,
    audience: str = "ALL_EMPLOYEES",
    top_k: int = 3,
    target_date: Optional[date] = None
) -> List[Dict[str, Any]]:
    """
    Search active knowledge articles valid on target_date and accessible to audience.
    Returns ranked articles with relevance scores.
    """
    check_date = target_date or date.today()

    # Query active policy versions
    query_obj = (
        db.query(KnowledgeArticle, PolicyVersion, PolicyDocument)
        .join(PolicyVersion, KnowledgeArticle.policy_version_id == PolicyVersion.version_id)
        .join(PolicyDocument, PolicyVersion.policy_id == PolicyDocument.policy_id)
        .filter(
            KnowledgeArticle.is_published == True,
            PolicyVersion.status == PolicyStatusEnum.ACTIVE,
            PolicyVersion.effective_from <= check_date
        )
    )

    # Filter out expired versions
    results = []
    for art, pver, pdoc in query_obj.all():
        if pver.effective_to and pver.effective_to < check_date:
            continue
        
        # Audience check: ALL_EMPLOYEES can see ALL_EMPLOYEES
        # If audience is restricted to MANAGERS_ONLY or HR_ONLY, check match
        if pdoc.audience.value not in ["ALL_EMPLOYEES", audience] and audience not in ["HR_ONLY", "MANAGERS_ONLY"]:
            continue

        searchable_text = f"{art.title} {art.keywords or ''} {art.content}"
        score = simple_token_similarity(query, searchable_text)

        # Keyword boost
        if art.keywords:
            for kw in art.keywords.split(","):
                if kw.strip().lower() in query.lower():
                    score += 0.25

        results.append({
            "article": art,
            "version": pver,
            "document": pdoc,
            "score": score
        })

    # Sort descending by score
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]

def generate_rag_answer(
    db: Session,
    query: str,
    audience: str = "ALL_EMPLOYEES",
    department_id: Optional[str] = None,
    category_id: Optional[str] = None,
    top_k: int = 3
) -> RAGQueryResponse:
    """
    Retrieve matching policy articles, format citations, and compose structured answer.
    """
    matches = search_knowledge_base(db, query, audience=audience, top_k=top_k)
    citations: List[CitationItem] = []

    if not matches or matches[0]["score"] == 0:
        return RAGQueryResponse(
            query=query,
            answer="We could not find an approved HR policy matching your inquiry. Please submit a request to an HR partner for personal assistance.",
            citations=[],
            is_ambiguous=False,
            clarification_question=None,
            confidence_score=0.20,
            model_used="RuleBasedFallback"
        )

    context_snippets = []
    for item in matches:
        art: KnowledgeArticle = item["article"]
        pver: PolicyVersion = item["version"]
        pdoc: PolicyDocument = item["document"]
        score = item["score"]

        # Extract quote
        sentences = re.split(r'(?<=[.!?]) +', art.content)
        best_sentence = sentences[0] if sentences else art.content[:150]
        for s in sentences:
            if any(w in s.lower() for w in re.findall(r'\w+', query.lower())):
                best_sentence = s.strip()
                break

        citation = CitationItem(
            policy_doc_code=pdoc.doc_code,
            policy_title=pdoc.title,
            version_number=pver.version_number,
            section_number=art.section_number,
            article_title=art.title,
            quote=best_sentence,
            relevance_score=round(score, 3)
        )
        citations.append(citation)
        context_snippets.append(
            f"[{pdoc.doc_code} v{pver.version_number} Sec {art.section_number} - {art.title}]: {art.content}"
        )

    # Check if Gemini API is available and configured
    answer_text = None
    model_name = "DeterministicPolicyEngine"

    if settings.GEMINI_API_KEY and HAS_GENAI:
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel(settings.GEMINI_MODEL)
            prompt = (
                f"You are an authoritative HR Assistant. Answer the employee's inquiry strictly based on the provided corporate policy excerpts. "
                f"Always cite the exact policy code, version, and section. If the excerpts do not contain the answer, say so.\n\n"
                f"Context Excerpts:\n" + "\n\n".join(context_snippets) + f"\n\nEmployee Query: {query}\n\nAnswer:"
            )
            response = model.generate_content(prompt)
            if response and response.text:
                answer_text = response.text.strip()
                model_name = f"Gemini ({settings.GEMINI_MODEL})"
        except Exception:
            answer_text = None

    # Fallback response generation
    if not answer_text:
        primary = matches[0]
        top_art: KnowledgeArticle = primary["article"]
        top_doc: PolicyDocument = primary["document"]
        top_ver: PolicyVersion = primary["version"]

        answer_text = (
            f"According to policy **{top_doc.title}** ({top_doc.doc_code}, Version {top_ver.version_number}, "
            f"Section {top_art.section_number}):\n\n"
            f"{top_art.content}\n\n"
            f"*Citation:* Verified against active policy version {top_ver.version_number} effective from {top_ver.effective_from}."
        )

    avg_score = sum(c.relevance_score for c in citations) / len(citations) if citations else 0.5
    confidence = min(0.98, max(0.60, avg_score + 0.35))

    return RAGQueryResponse(
        query=query,
        answer=answer_text,
        citations=citations,
        is_ambiguous=False,
        clarification_question=None,
        confidence_score=round(confidence, 2),
        model_used=model_name
    )

