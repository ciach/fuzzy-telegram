from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from backend.models.ai_interaction_model import AIInteractionRecord
from backend.models.contract_model import ContractRecord
from backend.models.log_model import LogRecord, TriggeredBy
from backend.schemas.contract_schema import (
    ContractSchema,
    SupportedLanguage,
    default_contract_schema,
    get_nested_value,
    update_contract_schema,
)
from backend.services.legal_notes_service import get_reference_clauses
from backend.services.logging_service import AuditLoggingService
from backend.storage.store_protocol import ContractStoreProtocol


class ContractNotFoundError(Exception):
    pass


class MutationValidationError(Exception):
    pass


class ManualClauseLockedError(Exception):
    pass


class ContractService:
    def __init__(self, store: ContractStoreProtocol, audit_logging_service: AuditLoggingService) -> None:
        self._store = store
        self._audit_logging_service = audit_logging_service

    def create_contract(self, language: SupportedLanguage, location: str) -> ContractRecord:
        now = datetime.now(timezone.utc)
        schema = default_contract_schema(language=language, location=location)
        schema.clauses = get_reference_clauses()
        record = ContractRecord(
            id=uuid4(),
            language=language,
            status="draft",
            schema_json=schema.model_dump(mode="json"),
            created_at=now,
            updated_at=now,
        )
        self._store.create_contract(record)
        return record

    def get_contract(self, contract_id: UUID) -> ContractRecord:
        contract = self._store.get_contract(contract_id)
        if contract is None:
            raise ContractNotFoundError(f"Contract {contract_id} not found")
        return contract

    def get_contract_schema(self, contract_id: UUID) -> ContractSchema:
        contract = self.get_contract(contract_id)
        return ContractSchema.model_validate(contract.schema_json)

    def get_logs(self, contract_id: UUID) -> list[LogRecord]:
        _ = self.get_contract(contract_id)
        return self._store.get_logs(contract_id)

    def apply_update(
        self,
        *,
        contract_id: UUID,
        path: str,
        value: Any,
        action_type: str,
        triggered_by: TriggeredBy,
        ai_prompt: str | None = None,
        ai_response: str | None = None,
        allow_manual_clause_override: bool = False,
    ) -> tuple[ContractRecord, LogRecord]:
        record = self.get_contract(contract_id)
        current_schema = ContractSchema.model_validate(record.schema_json)
        current_payload = current_schema.model_dump(mode="python")

        try:
            old_value = get_nested_value(current_payload, path)
        except KeyError as exc:
            raise MutationValidationError(f"Unknown path: {path}") from exc

        if path.startswith("clauses.") and triggered_by == "ai":
            clause_id = path.split(".", 1)[1]
            if self._store.has_manual_clause_edit(
                contract_id=contract_id,
                clause_id=clause_id,
            ) and not allow_manual_clause_override:
                raise ManualClauseLockedError(
                    f"Clause {clause_id} was manually edited and is locked for AI changes"
                )

        try:
            updated_schema = update_contract_schema(current_schema, path, value)
        except (ValueError, KeyError) as exc:
            raise MutationValidationError(str(exc)) from exc

        clause_version: tuple[str, str, str] | None = None
        if path.startswith("clauses."):
            clause_id = path.split(".", 1)[1]
            clause_version = (
                clause_id,
                str(get_nested_value(updated_schema.model_dump(mode="python"), path)),
                triggered_by,
            )

        record.schema_json = updated_schema.model_dump(mode="json")
        record.updated_at = datetime.now(timezone.utc)

        log_record = self._audit_logging_service.create_log(
            contract_id=contract_id,
            action_type=action_type,
            field_path=path,
            old_value=old_value,
            new_value=get_nested_value(updated_schema.model_dump(mode="python"), path),
            triggered_by=triggered_by,
            ai_prompt=ai_prompt,
            ai_response=ai_response,
        )
        self._store.persist_contract_mutation(
            record=record,
            log_record=log_record,
            clause_version=clause_version,
        )

        return record, log_record

    def log_ai_interaction(
        self,
        *,
        contract_id: UUID,
        prompt: str,
        raw_response: str | None,
        parsed_action: dict[str, Any] | None,
        status: str,
        error: str | None = None,
    ) -> AIInteractionRecord:
        _ = self.get_contract(contract_id)
        interaction = self._audit_logging_service.create_ai_interaction(
            contract_id=contract_id,
            prompt=prompt,
            raw_response=raw_response,
            parsed_action=parsed_action,
            status=status,
            error=error,
        )
        self._store.append_ai_interaction(contract_id, interaction)
        return interaction

    def get_ai_interactions(self, contract_id: UUID) -> list[AIInteractionRecord]:
        _ = self.get_contract(contract_id)
        return self._store.get_ai_interactions(contract_id)

    def rewrite_clause(
        self,
        *,
        contract_id: UUID,
        clause_id: str,
        new_text: str,
        triggered_by: TriggeredBy,
        ai_prompt: str | None = None,
        ai_response: str | None = None,
        allow_manual_clause_override: bool = False,
    ) -> tuple[ContractRecord, LogRecord]:
        return self.apply_update(
            contract_id=contract_id,
            path=f"clauses.{clause_id}",
            value=new_text,
            action_type="rewrite_clause",
            triggered_by=triggered_by,
            ai_prompt=ai_prompt,
            ai_response=ai_response,
            allow_manual_clause_override=allow_manual_clause_override,
        )
