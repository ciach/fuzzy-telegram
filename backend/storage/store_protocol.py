from __future__ import annotations

from typing import Protocol
from uuid import UUID

from backend.models.ai_interaction_model import AIInteractionRecord
from backend.models.contract_model import ContractRecord
from backend.models.log_model import LogRecord


class ContractStoreProtocol(Protocol):
    def create_contract(self, record: ContractRecord) -> None: ...

    def get_contract(self, contract_id: UUID) -> ContractRecord | None: ...

    def update_contract(self, record: ContractRecord) -> None: ...

    def append_log(self, contract_id: UUID, log_record: LogRecord) -> None: ...

    def get_logs(self, contract_id: UUID) -> list[LogRecord]: ...

    def append_clause_version(self, *, contract_id: UUID, clause_id: str, content: str, triggered_by: str) -> None: ...

    def has_manual_clause_edit(self, *, contract_id: UUID, clause_id: str) -> bool: ...

    def append_ai_interaction(self, contract_id: UUID, interaction: AIInteractionRecord) -> None: ...

    def get_ai_interactions(self, contract_id: UUID) -> list[AIInteractionRecord]: ...

    def persist_contract_mutation(
        self,
        *,
        record: ContractRecord,
        log_record: LogRecord,
        clause_version: tuple[str, str, str] | None,
    ) -> None: ...
