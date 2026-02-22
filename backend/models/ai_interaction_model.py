from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(slots=True)
class AIInteractionRecord:
    id: UUID
    contract_id: UUID
    prompt: str
    raw_response: str | None
    parsed_action: dict[str, Any] | None
    status: str
    error: str | None
    created_at: datetime

