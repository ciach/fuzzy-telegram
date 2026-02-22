from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, JSON, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base


jsonb_type = JSONB().with_variant(JSON(), "sqlite")


class ContractORM(Base):
    __tablename__ = "contracts"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    language: Mapped[str] = mapped_column(String(8), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="draft")
    schema_json: Mapped[dict[str, Any]] = mapped_column(jsonb_type, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class ContractLogORM(Base):
    __tablename__ = "contract_logs"
    __table_args__ = (Index("ix_contract_logs_contract_id_created_at", "contract_id", "created_at"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    contract_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False)
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)
    field_path: Mapped[str | None] = mapped_column(String(256), nullable=True)
    old_value: Mapped[Any] = mapped_column(jsonb_type, nullable=True)
    new_value: Mapped[Any] = mapped_column(jsonb_type, nullable=True)
    triggered_by: Mapped[str] = mapped_column(String(16), nullable=False)
    ai_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ClauseVersionORM(Base):
    __tablename__ = "clause_versions"
    __table_args__ = (Index("ix_clause_versions_contract_clause", "contract_id", "clause_id"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    contract_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False)
    clause_id: Mapped[str] = mapped_column(String(64), nullable=False)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    triggered_by: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class AIInteractionORM(Base):
    __tablename__ = "ai_interactions"
    __table_args__ = (Index("ix_ai_interactions_contract_id_created_at", "contract_id", "created_at"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    contract_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    raw_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    parsed_action: Mapped[dict[str, Any] | None] = mapped_column(jsonb_type, nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

