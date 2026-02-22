from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

TriggeredBy = Literal["user", "ai"]


@dataclass(slots=True)
class ClauseVersionRecord:
    id: UUID
    contract_id: UUID
    clause_id: str
    version_no: int
    content: str
    triggered_by: TriggeredBy
    created_at: datetime

