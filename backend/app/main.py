"""
HR Request Resolution System - Main Application Entrypoint
FastAPI Backend Application
"""
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from app.core.config import settings
from app.routes import api_router
from app.database.session import engine
from app.database.base import Base
# Import all models to ensure metadata registration
import app.models

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="""
# Enterprise HR Request Resolution System API

Welcome to the **HR Request Resolution System** API.

### Features
- **Deterministic Business-Hours SLA Engine**: Accurately tracks response and resolution deadlines (Mon-Fri 09:00 - 17:00).
- **RAG & Policy QA with Exact Citations**: Gemini & Local semantic search over versioned corporate policies.
- **Ambiguity & Sensitivity Triage**: Proactively flags vague inquiries and confidentially routes sensitive cases.
- **Audit Logging & Anomaly Detection**: Comprehensive tracking for obsolete policy citations, SLA miscalculations, and security breaches.

### Authentication
Click the **Authorize** button on the right to authenticate.
- **Format**: `Bearer <token>` or login using your email and password.
- **Demo Accounts**:
  - Employee: `john.doe@company.com` / `Password123!`
  - HR Agent: `sarah.agent@company.com` / `Password123!`
  - HR Manager: `emily.manager@company.com` / `Password123!`
  - Admin: `admin@company.com` / `Password123!`
  - Compliance: `rachel.compliance@company.com` / `Password123!`
    """,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

@app.get("/", include_in_schema=False)
def root_redirect():
    return RedirectResponse(url="/docs")


@app.on_event("startup")
def on_startup():
    try:
        # Create tables automatically if using SQLite fallback, or ensure schema ready
        Base.metadata.create_all(bind=engine)
    except Exception:
        # In MySQL mode, schema is managed via schema.sql or migrations
        pass

