"""
Routes Package Initialization
"""
from fastapi import APIRouter
from app.routes.auth import router as auth_router
from app.routes.employees import router as employees_router
from app.routes.departments import router as departments_router
from app.routes.categories import router as categories_router
from app.routes.tickets import router as tickets_router
from app.routes.policies import router as policies_router
from app.routes.rag import router as rag_router
from app.routes.sla import router as sla_router
from app.routes.analytics import router as analytics_router
from app.routes.anomalies import router as anomalies_router
from app.routes.audit import router as audit_router
from app.routes.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(employees_router)
api_router.include_router(departments_router)
api_router.include_router(categories_router)
api_router.include_router(tickets_router)
api_router.include_router(policies_router)
api_router.include_router(rag_router)
api_router.include_router(sla_router)
api_router.include_router(analytics_router)
api_router.include_router(anomalies_router)
api_router.include_router(audit_router)

__all__ = ["api_router"]

