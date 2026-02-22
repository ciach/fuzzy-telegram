from __future__ import annotations

from backend.models.ai_interaction_model import AIInteractionRecord
from backend.models.contract_model import ContractRecord
from backend.models.log_model import LogRecord
from backend.schemas.contract_schema import AIInteractionView, ContractLogView, ContractSchema, ContractView


def to_contract_view(record: ContractRecord) -> ContractView:
    return ContractView(
        id=record.id,
        language=record.language,
        status=record.status,
        contract_schema=ContractSchema.model_validate(record.schema_json),
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def to_log_view(record: LogRecord) -> ContractLogView:
    return ContractLogView(
        id=record.id,
        contract_id=record.contract_id,
        action_type=record.action_type,
        field_path=record.field_path,
        old_value=record.old_value,
        new_value=record.new_value,
        triggered_by=record.triggered_by,
        ai_prompt=record.ai_prompt,
        ai_response=record.ai_response,
        created_at=record.created_at,
    )


def to_ai_interaction_view(record: AIInteractionRecord) -> AIInteractionView:
    return AIInteractionView(
        id=record.id,
        contract_id=record.contract_id,
        prompt=record.prompt,
        raw_response=record.raw_response,
        parsed_action=record.parsed_action,
        status=record.status,
        error=record.error,
        created_at=record.created_at,
    )
