from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

SupportedLanguage = Literal["es", "ca", "en"]
ContractStatus = Literal["draft", "finalized"]


@dataclass(slots=True)
class ContractRecord:
    id: UUID
    language: SupportedLanguage
    status: ContractStatus
    schema_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime

