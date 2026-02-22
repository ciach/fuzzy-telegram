from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

TriggeredBy = Literal["user", "ai"]


@dataclass(slots=True)
class LogRecord:
    id: UUID
    contract_id: UUID
    action_type: str
    field_path: str | None
    old_value: Any
    new_value: Any
    triggered_by: TriggeredBy
    ai_prompt: str | None
    ai_response: str | None
    created_at: datetime

