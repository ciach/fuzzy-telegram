from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable
from uuid import UUID

from sqlalchemy import Select, desc, func, select
from sqlalchemy.orm import Session

from backend.db.models import AIInteractionORM, ClauseVersionORM, ContractLogORM, ContractORM
from backend.models.ai_interaction_model import AIInteractionRecord
from backend.models.contract_model import ContractRecord
from backend.models.log_model import LogRecord


class SQLAlchemyStore:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def create_contract(self, record: ContractRecord) -> None:
        with self._session_factory() as session:
            orm = ContractORM(
                id=record.id,
                language=record.language,
                status=record.status,
                schema_json=record.schema_json,
                created_at=record.created_at,
                updated_at=record.updated_at,
            )
            session.add(orm)
            session.commit()

    def get_contract(self, contract_id: UUID) -> ContractRecord | None:
        with self._session_factory() as session:
            orm = session.get(ContractORM, contract_id)
            if orm is None:
                return None
            return self._to_contract_record(orm)

    def update_contract(self, record: ContractRecord) -> None:
        with self._session_factory() as session:
            orm = session.get(ContractORM, record.id)
            if orm is None:
                return
            orm.language = record.language
            orm.status = record.status
            orm.schema_json = record.schema_json
            orm.updated_at = record.updated_at
            session.add(orm)
            session.commit()

    def append_log(self, contract_id: UUID, log_record: LogRecord) -> None:
        with self._session_factory() as session:
            orm = ContractLogORM(
                id=log_record.id,
                contract_id=contract_id,
                action_type=log_record.action_type,
                field_path=log_record.field_path,
                old_value=log_record.old_value,
                new_value=log_record.new_value,
                triggered_by=log_record.triggered_by,
                ai_prompt=log_record.ai_prompt,
                ai_response=log_record.ai_response,
                created_at=log_record.created_at,
            )
            session.add(orm)
            session.commit()

    def get_logs(self, contract_id: UUID) -> list[LogRecord]:
        with self._session_factory() as session:
            stmt: Select[tuple[ContractLogORM]] = (
                select(ContractLogORM)
                .where(ContractLogORM.contract_id == contract_id)
                .order_by(ContractLogORM.created_at.asc(), ContractLogORM.id.asc())
            )
            rows = session.execute(stmt).scalars().all()
            return [self._to_log_record(row) for row in rows]

    def append_clause_version(self, *, contract_id: UUID, clause_id: str, content: str, triggered_by: str) -> None:
        with self._session_factory() as session:
            stmt = select(func.max(ClauseVersionORM.version_no)).where(
                ClauseVersionORM.contract_id == contract_id,
                ClauseVersionORM.clause_id == clause_id,
            )
            latest_version = session.execute(stmt).scalar_one_or_none() or 0
            orm = ClauseVersionORM(
                contract_id=contract_id,
                clause_id=clause_id,
                version_no=int(latest_version) + 1,
                content=content,
                triggered_by=triggered_by,
            )
            session.add(orm)
            session.commit()

    def has_manual_clause_edit(self, *, contract_id: UUID, clause_id: str) -> bool:
        with self._session_factory() as session:
            stmt = (
                select(ClauseVersionORM.id)
                .where(
                    ClauseVersionORM.contract_id == contract_id,
                    ClauseVersionORM.clause_id == clause_id,
                    ClauseVersionORM.triggered_by == "user",
                )
                .limit(1)
            )
            return session.execute(stmt).scalar_one_or_none() is not None

    def append_ai_interaction(self, contract_id: UUID, interaction: AIInteractionRecord) -> None:
        with self._session_factory() as session:
            orm = AIInteractionORM(
                id=interaction.id,
                contract_id=contract_id,
                prompt=interaction.prompt,
                raw_response=interaction.raw_response,
                parsed_action=interaction.parsed_action,
                status=interaction.status,
                error=interaction.error,
                created_at=interaction.created_at,
            )
            session.add(orm)
            session.commit()

    def get_ai_interactions(self, contract_id: UUID) -> list[AIInteractionRecord]:
        with self._session_factory() as session:
            stmt = (
                select(AIInteractionORM)
                .where(AIInteractionORM.contract_id == contract_id)
                .order_by(desc(AIInteractionORM.created_at), desc(AIInteractionORM.id))
            )
            rows = session.execute(stmt).scalars().all()
            return [self._to_ai_interaction_record(row) for row in rows]

    def persist_contract_mutation(
        self,
        *,
        record: ContractRecord,
        log_record: LogRecord,
        clause_version: tuple[str, str, str] | None,
    ) -> None:
        with self._session_factory() as session:
            orm = session.get(ContractORM, record.id)
            if orm is None:
                return
            orm.language = record.language
            orm.status = record.status
            orm.schema_json = record.schema_json
            orm.updated_at = record.updated_at
            session.add(orm)

            log_orm = ContractLogORM(
                id=log_record.id,
                contract_id=record.id,
                action_type=log_record.action_type,
                field_path=log_record.field_path,
                old_value=log_record.old_value,
                new_value=log_record.new_value,
                triggered_by=log_record.triggered_by,
                ai_prompt=log_record.ai_prompt,
                ai_response=log_record.ai_response,
                created_at=log_record.created_at,
            )
            session.add(log_orm)

            if clause_version is not None:
                clause_id, content, triggered_by = clause_version
                stmt = select(func.max(ClauseVersionORM.version_no)).where(
                    ClauseVersionORM.contract_id == record.id,
                    ClauseVersionORM.clause_id == clause_id,
                )
                latest_version = session.execute(stmt).scalar_one_or_none() or 0
                clause_orm = ClauseVersionORM(
                    contract_id=record.id,
                    clause_id=clause_id,
                    version_no=int(latest_version) + 1,
                    content=content,
                    triggered_by=triggered_by,
                )
                session.add(clause_orm)

            session.commit()

    @staticmethod
    def _to_contract_record(orm: ContractORM) -> ContractRecord:
        return ContractRecord(
            id=orm.id,
            language=orm.language,  # type: ignore[arg-type]
            status=orm.status,  # type: ignore[arg-type]
            schema_json=orm.schema_json,
            created_at=_normalize_dt(orm.created_at),
            updated_at=_normalize_dt(orm.updated_at),
        )

    @staticmethod
    def _to_log_record(orm: ContractLogORM) -> LogRecord:
        return LogRecord(
            id=orm.id,
            contract_id=orm.contract_id,
            action_type=orm.action_type,
            field_path=orm.field_path,
            old_value=orm.old_value,
            new_value=orm.new_value,
            triggered_by=orm.triggered_by,  # type: ignore[arg-type]
            ai_prompt=orm.ai_prompt,
            ai_response=orm.ai_response,
            created_at=_normalize_dt(orm.created_at),
        )

    @staticmethod
    def _to_ai_interaction_record(orm: AIInteractionORM) -> AIInteractionRecord:
        return AIInteractionRecord(
            id=orm.id,
            contract_id=orm.contract_id,
            prompt=orm.prompt,
            raw_response=orm.raw_response,
            parsed_action=orm.parsed_action,
            status=orm.status,
            error=orm.error,
            created_at=_normalize_dt(orm.created_at),
        )


def _normalize_dt(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value
