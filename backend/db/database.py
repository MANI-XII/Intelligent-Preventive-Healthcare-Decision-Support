from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.config import settings


def _build_database_url() -> str:
    if settings.postgres_url.strip():
        return settings.postgres_url.strip()

    # Local fallback for quick local development.
    # (If you want strict PostgreSQL-only, set POSTGRES_URL and disable SQLite fallback.)
    return "sqlite:///./backend/app.db"


DATABASE_URL = _build_database_url()

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, echo=settings.db_echo, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

