from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.core.config import get_settings
from backend.db.base import Base


settings = get_settings()
engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, class_=Session)
_schema_initialized = False


def create_all_tables() -> None:
    Base.metadata.create_all(bind=engine)


def get_session() -> Session:
    return SessionLocal()


def ensure_schema_ready() -> None:
    global _schema_initialized
    if _schema_initialized:
        return
    if settings.auto_create_schema:
        create_all_tables()
    _schema_initialized = True
