"""
Database Session Management Module
Configures SQLAlchemy engine, session factory, and FastAPI dependency.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

def get_engine():
    """Create SQLAlchemy engine with connection pool settings."""
    url = settings.get_database_url
    if "sqlite" in url:
        return create_engine(
            url,
            connect_args={"check_same_thread": False}
        )
    return create_engine(
        url,
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_size=10,
        max_overflow=20
    )

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """FastAPI dependency for obtaining a database session per request."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

