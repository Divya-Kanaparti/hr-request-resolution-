"""
Schemas Package Initialization
"""
from app.schemas.auth import LoginRequest, TokenResponse, RegisterRequest, UserSummary
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse
from app.schemas.department import DepartmentCreate, DepartmentResponse
from app.schemas.category import CategoryCreate, CategoryResponse
from app.schemas.policy import (
    PolicyDocumentCreate, PolicyDocumentResponse,
    PolicyVersionCreate, PolicyVersionResponse,
    KnowledgeArticleCreate, KnowledgeArticleResponse
)
from app.schemas.ticket import (
    TicketCreate, TicketUpdate, TicketResponse, TicketDetailResponse,
    TicketAssignRequest, TicketEscalateRequest,
    ClassificationResult, AmbiguityCheckResult
)
from app.schemas.assignment import AssignmentCreate, AssignmentResponse
from app.schemas.sla import SLAResponse, SLACheckResult
from app.schemas.message import MessageCreate, MessageResponse
from app.schemas.resolution import ResolutionCreate, ResolutionResponse, SatisfactionRatingRequest
from app.schemas.rag import RAGQueryRequest, RAGQueryResponse, CitationItem
from app.schemas.analytics import (
    DashboardSummaryResponse, CategoryDistribution, StatusDistribution,
    PriorityDistribution, SLAComplianceMetrics, AgentWorkload, AnomalySummary
)
from app.schemas.anomaly import AnomalyResponse, AnomalyResolveRequest
from app.schemas.audit import AuditLogResponse

__all__ = [
    "LoginRequest", "TokenResponse", "RegisterRequest", "UserSummary",
    "EmployeeCreate", "EmployeeUpdate", "EmployeeResponse",
    "DepartmentCreate", "DepartmentResponse",
    "CategoryCreate", "CategoryResponse",
    "PolicyDocumentCreate", "PolicyDocumentResponse",
    "PolicyVersionCreate", "PolicyVersionResponse",
    "KnowledgeArticleCreate", "KnowledgeArticleResponse",
    "TicketCreate", "TicketUpdate", "TicketResponse", "TicketDetailResponse",
    "TicketAssignRequest", "TicketEscalateRequest",
    "ClassificationResult", "AmbiguityCheckResult",
    "AssignmentCreate", "AssignmentResponse",
    "SLAResponse", "SLACheckResult",
    "MessageCreate", "MessageResponse",
    "ResolutionCreate", "ResolutionResponse", "SatisfactionRatingRequest",
    "RAGQueryRequest", "RAGQueryResponse", "CitationItem",
    "DashboardSummaryResponse", "CategoryDistribution", "StatusDistribution",
    "PriorityDistribution", "SLAComplianceMetrics", "AgentWorkload", "AnomalySummary",
    "AnomalyResponse", "AnomalyResolveRequest",
    "AuditLogResponse"
]

