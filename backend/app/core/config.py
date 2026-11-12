"""
Application Configuration Module
Loads settings from environment variables or .env file with defaults.
Includes graceful fallback if Pydantic binary DLL is restricted by Windows Application Control.
"""
import os
from pathlib import Path
from typing import List

try:
    from pydantic_settings import BaseSettings

    class Settings(BaseSettings):
        APP_NAME: str = "HR Request Resolution System"
        APP_ENV: str = "development"
        DEBUG: bool = True
        API_V1_PREFIX: str = "/api/v1"
        
        # Security
        SECRET_KEY: str = "hr-resolution-super-secret-key-change-in-production-2026"
        ALGORITHM: str = "HS256"
        ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
        
        # Database
        DB_HOST: str = "localhost"
        DB_PORT: int = 3306
        DB_USER: str = "root"
        DB_PASSWORD: str = "root"
        DB_NAME: str = "hr_request_resolution"
        DATABASE_URL: str = ""
        
        # Business Hours & SLA (24h)
        BUSINESS_HOUR_START: int = 9   # 9:00 AM
        BUSINESS_HOUR_END: int = 17    # 5:00 PM
        WORK_DAYS: str = "0,1,2,3,4"   # Mon-Fri
        DEFAULT_RESPONSE_HOURS: int = 4
        DEFAULT_RESOLUTION_HOURS: int = 24
        HIGH_PRIORITY_RESOLUTION_HOURS: int = 8
        URGENT_PRIORITY_RESOLUTION_HOURS: int = 4
        
        # AI & RAG
        GEMINI_API_KEY: str = ""
        GEMINI_MODEL: str = "gemini-1.5-flash"
        EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
        CHROMA_PERSIST_DIRECTORY: str = "./chroma_db"
        USE_MOCK_LLM_FALLBACK: bool = True
        
        # Random Seed
        RANDOM_SEED: int = 20261022

        @property
        def get_database_url(self) -> str:
            if self.DATABASE_URL:
                return self.DATABASE_URL
            return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

        @property
        def parsed_work_days(self) -> List[int]:
            return [int(d.strip()) for d in self.WORK_DAYS.split(",") if d.strip().isdigit()]

        class Config:
            env_file = ".env"
            extra = "ignore"

    settings = Settings()

except Exception:
    # Pure-Python fallback when Pydantic C/Rust DLL is blocked by OS Application Control
    class PureSettings:
        def __init__(self):
            self.APP_NAME = "HR Request Resolution System"
            self.APP_ENV = "development"
            self.DEBUG = True
            self.API_V1_PREFIX = "/api/v1"
            self.SECRET_KEY = "hr-resolution-super-secret-key-change-in-production-2026"
            self.ALGORITHM = "HS256"
            self.ACCESS_TOKEN_EXPIRE_MINUTES = 480
            self.DB_HOST = "localhost"
            self.DB_PORT = 3306
            self.DB_USER = "root"
            self.DB_PASSWORD = "root"
            self.DB_NAME = "hr_request_resolution"
            self.DATABASE_URL = ""
            self.BUSINESS_HOUR_START = 9
            self.BUSINESS_HOUR_END = 17
            self.WORK_DAYS = "0,1,2,3,4"
            self.DEFAULT_RESPONSE_HOURS = 4
            self.DEFAULT_RESOLUTION_HOURS = 24
            self.HIGH_PRIORITY_RESOLUTION_HOURS = 8
            self.URGENT_PRIORITY_RESOLUTION_HOURS = 4
            self.GEMINI_API_KEY = ""
            self.GEMINI_MODEL = "gemini-1.5-flash"
            self.EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
            self.CHROMA_PERSIST_DIRECTORY = "./chroma_db"
            self.USE_MOCK_LLM_FALLBACK = True
            self.RANDOM_SEED = 20261022
            self._load_from_env()

        def _load_from_env(self):
            for candidate in [Path(".env"), Path("../.env"), Path(__file__).resolve().parent.parent.parent.parent / ".env"]:
                if candidate.exists():
                    with open(candidate, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith("#") and "=" in line:
                                k, v = line.split("=", 1)
                                k = k.strip()
                                v = v.strip().strip('"').strip("'")
                                if hasattr(self, k):
                                    cur = getattr(self, k)
                                    if isinstance(cur, bool):
                                        setattr(self, k, v.lower() in ["true", "1", "yes"])
                                    elif isinstance(cur, int):
                                        try: setattr(self, k, int(v))
                                        except: pass
                                    else:
                                        setattr(self, k, v)
                    break

        @property
        def get_database_url(self) -> str:
            if self.DATABASE_URL:
                return self.DATABASE_URL
            return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

        @property
        def parsed_work_days(self) -> List[int]:
            return [int(d.strip()) for d in self.WORK_DAYS.split(",") if d.strip().isdigit()]

    settings = PureSettings()
