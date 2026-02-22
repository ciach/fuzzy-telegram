from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from rich.logging import RichHandler

from backend.models.ai_interaction_model import AIInteractionRecord
from backend.models.log_model import LogRecord, TriggeredBy


def configure_app_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)],
    )


class AuditLoggingService:
    def create_log(
        self,
        *,
        contract_id: UUID,
        action_type: str,
        field_path: str | None,
        old_value: Any,
        new_value: Any,
        triggered_by: TriggeredBy,
        ai_prompt: str | None = None,
        ai_response: str | None = None,
    ) -> LogRecord:
        return LogRecord(
            id=uuid4(),
            contract_id=contract_id,
            action_type=action_type,
            field_path=field_path,
            old_value=old_value,
            new_value=new_value,
            triggered_by=triggered_by,
            ai_prompt=ai_prompt,
            ai_response=ai_response,
            created_at=datetime.now(timezone.utc),
        )

    def create_ai_interaction(
        self,
        *,
        contract_id: UUID,
        prompt: str,
        raw_response: str | None,
        parsed_action: dict[str, Any] | None,
        status: str,
        error: str | None = None,
    ) -> AIInteractionRecord:
        return AIInteractionRecord(
            id=uuid4(),
            contract_id=contract_id,
            prompt=prompt,
            raw_response=raw_response,
            parsed_action=parsed_action,
            status=status,
            error=error,
            created_at=datetime.now(timezone.utc),
        )
