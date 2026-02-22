from __future__ import annotations

from threading import Lock
from uuid import UUID

from backend.models.ai_interaction_model import AIInteractionRecord
from backend.models.contract_model import ContractRecord
from backend.models.log_model import LogRecord


class InMemoryStore:
    def __init__(self) -> None:
        self._contracts: dict[UUID, ContractRecord] = {}
        self._logs: dict[UUID, list[LogRecord]] = {}
        self._clause_versions: dict[UUID, dict[str, list[dict[str, str]]]] = {}
        self._ai_interactions: dict[UUID, list[AIInteractionRecord]] = {}
        self._lock = Lock()

    def create_contract(self, record: ContractRecord) -> None:
        with self._lock:
            self._contracts[record.id] = record
            self._logs.setdefault(record.id, [])
            self._clause_versions.setdefault(record.id, {})
            self._ai_interactions.setdefault(record.id, [])

    def get_contract(self, contract_id: UUID) -> ContractRecord | None:
        with self._lock:
            return self._contracts.get(contract_id)

    def update_contract(self, record: ContractRecord) -> None:
        with self._lock:
            self._contracts[record.id] = record

    def append_log(self, contract_id: UUID, log_record: LogRecord) -> None:
        with self._lock:
            self._logs.setdefault(contract_id, []).append(log_record)

    def get_logs(self, contract_id: UUID) -> list[LogRecord]:
        with self._lock:
            return list(self._logs.get(contract_id, []))

    def append_clause_version(self, *, contract_id: UUID, clause_id: str, content: str, triggered_by: str) -> None:
        with self._lock:
            clauses = self._clause_versions.setdefault(contract_id, {})
            clauses.setdefault(clause_id, []).append({"content": content, "triggered_by": triggered_by})

    def has_manual_clause_edit(self, *, contract_id: UUID, clause_id: str) -> bool:
        with self._lock:
            clauses = self._clause_versions.get(contract_id, {})
            versions = clauses.get(clause_id, [])
            return any(item["triggered_by"] == "user" for item in versions)

    def append_ai_interaction(self, contract_id: UUID, interaction: AIInteractionRecord) -> None:
        with self._lock:
            self._ai_interactions.setdefault(contract_id, []).append(interaction)

    def get_ai_interactions(self, contract_id: UUID) -> list[AIInteractionRecord]:
        with self._lock:
            return list(self._ai_interactions.get(contract_id, []))

    def persist_contract_mutation(
        self,
        *,
        record: ContractRecord,
        log_record: LogRecord,
        clause_version: tuple[str, str, str] | None,
    ) -> None:
        with self._lock:
            self._contracts[record.id] = record
            self._logs.setdefault(record.id, []).append(log_record)
            if clause_version is not None:
                clause_id, content, triggered_by = clause_version
                clauses = self._clause_versions.setdefault(record.id, {})
                clauses.setdefault(clause_id, []).append({"content": content, "triggered_by": triggered_by})
