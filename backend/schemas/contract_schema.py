from __future__ import annotations

from copy import deepcopy
from datetime import date as dt_date
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

SupportedLanguage = Literal["es", "ca", "en"]
ContractStatus = Literal["draft", "finalized"]
TriggeredBy = Literal["user", "ai"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class Metadata(StrictModel):
    location: str = "Barcelona"
    date: dt_date = Field(default_factory=dt_date.today)
    language: SupportedLanguage = "es"


class Party(StrictModel):
    full_name: str
    id_number: str | None = None


class Parties(StrictModel):
    sellers: list[Party] = Field(default_factory=list)
    buyers: list[Party] = Field(default_factory=list)


class Property(StrictModel):
    address: str = ""
    registry: str = ""
    cargas: list[str] = Field(default_factory=list)
    ibi: float = Field(default=0.0, ge=0)


class Financial(StrictModel):
    total_price: float = Field(default=0.0, ge=0)
    arras_amount: float = Field(default=0.0, ge=0)
    remaining_amount: float = Field(default=0.0, ge=0)
    deadline: dt_date | None = None

    @model_validator(mode="after")
    def compute_remaining(self) -> "Financial":
        if self.arras_amount > self.total_price:
            raise ValueError("arras_amount cannot exceed total_price")
        self.remaining_amount = round(self.total_price - self.arras_amount, 2)
        return self


class ContractSchema(StrictModel):
    metadata: Metadata = Field(default_factory=Metadata)
    parties: Parties = Field(default_factory=Parties)
    property: Property = Field(default_factory=Property)
    financial: Financial = Field(default_factory=Financial)
    clauses: dict[str, str] = Field(
        default_factory=lambda: {
            "clause_1": "",
            "clause_2": "",
            "clause_3": "",
        }
    )


class CreateContractRequest(StrictModel):
    language: SupportedLanguage = "es"
    location: str = "Barcelona"


class ContractMutationRequest(StrictModel):
    path: str
    value: Any


class ChatRequest(StrictModel):
    message: str
    allow_manual_clause_override: bool = False


class ContractView(StrictModel):
    id: UUID
    language: SupportedLanguage
    status: ContractStatus
    contract_schema: ContractSchema = Field(alias="schema")
    created_at: datetime
    updated_at: datetime


class ContractLogView(StrictModel):
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


class AIInteractionView(StrictModel):
    id: UUID
    contract_id: UUID
    prompt: str
    raw_response: str | None
    parsed_action: dict[str, Any] | None
    status: str
    error: str | None
    created_at: datetime


def default_contract_schema(language: SupportedLanguage, location: str = "Barcelona") -> ContractSchema:
    schema = ContractSchema(
        metadata=Metadata(language=language, location=location),
        financial=Financial(total_price=0, arras_amount=0, remaining_amount=0),
    )
    return schema


def get_nested_value(payload: dict[str, Any], path: str) -> Any:
    parts = path.split(".")
    current: Any = payload
    for part in parts:
        if not isinstance(current, dict) or part not in current:
            raise KeyError(path)
        current = current[part]
    return current


def _set_nested_value(payload: dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    current: Any = payload
    for part in parts[:-1]:
        if not isinstance(current, dict) or part not in current:
            raise KeyError(path)
        current = current[part]
    final_key = parts[-1]
    if not isinstance(current, dict) or final_key not in current:
        raise KeyError(path)
    current[final_key] = value


def update_contract_schema(schema: ContractSchema, path: str, value: Any) -> ContractSchema:
    if path == "financial.remaining_amount":
        raise ValueError("financial.remaining_amount is derived and cannot be set directly")

    raw = deepcopy(schema.model_dump(mode="python"))
    _set_nested_value(raw, path, value)
    return ContractSchema.model_validate(raw)
