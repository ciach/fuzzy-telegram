from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from backend.api.presenters import to_ai_interaction_view, to_contract_view
from backend.dependencies import get_ai_service, get_contract_service
from backend.schemas.ai_actions import AIAction, NoAction, RewriteClauseAction, UpdateFieldAction
from backend.schemas.contract_schema import AIInteractionView, ChatRequest, ContractView
from backend.services.ai_service import AIService
from backend.services.contract_service import (
    ContractNotFoundError,
    ContractService,
    ManualClauseLockedError,
    MutationValidationError,
)

router = APIRouter(prefix="/contracts", tags=["chat"])


class ChatResult(BaseModel):
    action: AIAction
    applied: bool
    interaction_id: UUID
    contract: ContractView | None = None
    reason: str | None = None


class VoiceUpdateResult(BaseModel):
    path: str
    applied: bool
    error: str | None = None


class VoiceIntakeResult(BaseModel):
    transcript: str
    updates: list[VoiceUpdateResult]
    applied_count: int
    interaction_id: UUID
    contract: ContractView
    reason: str | None = None


@router.post("/{contract_id}/chat", response_model=ChatResult)
async def chat_mutation(
    contract_id: UUID,
    payload: ChatRequest,
    contract_service: ContractService = Depends(get_contract_service),
    ai_service: AIService = Depends(get_ai_service),
) -> ChatResult:
    try:
        schema = contract_service.get_contract_schema(contract_id)
    except ContractNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    action, raw_response = await ai_service.propose_action(user_message=payload.message, contract=schema)
    parsed_action = action.model_dump(mode="json")

    if isinstance(action, NoAction):
        interaction = contract_service.log_ai_interaction(
            contract_id=contract_id,
            prompt=payload.message,
            raw_response=raw_response,
            parsed_action=parsed_action,
            status=action.reason,
        )
        return ChatResult(action=action, applied=False, reason=action.reason, interaction_id=interaction.id)

    try:
        if isinstance(action, UpdateFieldAction):
            record, _ = contract_service.apply_update(
                contract_id=contract_id,
                path=action.path,
                value=action.value,
                action_type=action.action,
                triggered_by="ai",
                ai_prompt=payload.message,
                ai_response=raw_response,
                allow_manual_clause_override=payload.allow_manual_clause_override,
            )
        elif isinstance(action, RewriteClauseAction):
            record, _ = contract_service.rewrite_clause(
                contract_id=contract_id,
                clause_id=action.clause_id,
                new_text=action.new_text,
                triggered_by="ai",
                ai_prompt=payload.message,
                ai_response=raw_response,
                allow_manual_clause_override=payload.allow_manual_clause_override,
            )
        else:
            interaction = contract_service.log_ai_interaction(
                contract_id=contract_id,
                prompt=payload.message,
                raw_response=raw_response,
                parsed_action=parsed_action,
                status="unsupported_action",
            )
            return ChatResult(
                action=NoAction(action="no_action", reason="unsupported_action"),
                applied=False,
                interaction_id=interaction.id,
            )
        interaction = contract_service.log_ai_interaction(
            contract_id=contract_id,
            prompt=payload.message,
            raw_response=raw_response,
            parsed_action=parsed_action,
            status="applied",
        )
    except ContractNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ManualClauseLockedError as exc:
        contract_service.log_ai_interaction(
            contract_id=contract_id,
            prompt=payload.message,
            raw_response=raw_response,
            parsed_action=parsed_action,
            status="rejected_manual_clause_lock",
            error=str(exc),
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except MutationValidationError as exc:
        contract_service.log_ai_interaction(
            contract_id=contract_id,
            prompt=payload.message,
            raw_response=raw_response,
            parsed_action=parsed_action,
            status="rejected_validation",
            error=str(exc),
        )
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    return ChatResult(action=action, applied=True, contract=to_contract_view(record), interaction_id=interaction.id)


@router.post("/{contract_id}/voice-intake", response_model=VoiceIntakeResult)
async def voice_intake(
    contract_id: UUID,
    audio_file: UploadFile = File(...),
    contract_service: ContractService = Depends(get_contract_service),
    ai_service: AIService = Depends(get_ai_service),
) -> VoiceIntakeResult:
    try:
        schema = contract_service.get_contract_schema(contract_id)
    except ContractNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    audio_bytes = await audio_file.read()
    transcript = await ai_service.transcribe_audio(
        audio_bytes=audio_bytes,
        filename=audio_file.filename or "voice.webm",
        language=schema.metadata.language,
    )
    updates, raw_response, reason = await ai_service.propose_updates_from_transcript(
        transcript=transcript,
        contract=schema,
    )

    results: list[VoiceUpdateResult] = []
    last_record = contract_service.get_contract(contract_id)
    for item in updates:
        try:
            last_record, _ = contract_service.apply_update(
                contract_id=contract_id,
                path=item.path,
                value=item.value,
                action_type="voice_update_field",
                triggered_by="ai",
                ai_prompt=f"voice_transcript: {transcript}",
                ai_response=raw_response,
            )
            results.append(VoiceUpdateResult(path=item.path, applied=True))
        except MutationValidationError as exc:
            results.append(VoiceUpdateResult(path=item.path, applied=False, error=str(exc)))
        except ManualClauseLockedError as exc:
            results.append(VoiceUpdateResult(path=item.path, applied=False, error=str(exc)))

    applied_count = sum(1 for item in results if item.applied)
    status_label = (
        "voice_applied"
        if applied_count and applied_count == len(results)
        else "voice_applied_partial"
        if applied_count
        else f"voice_no_updates:{reason or 'no_updates'}"
    )

    interaction = contract_service.log_ai_interaction(
        contract_id=contract_id,
        prompt=f"voice_transcript: {transcript}",
        raw_response=raw_response,
        parsed_action={
            "transcript": transcript,
            "updates": [item.model_dump(mode="json") for item in updates],
            "results": [item.model_dump(mode="json") for item in results],
            "reason": reason,
        },
        status=status_label,
    )

    return VoiceIntakeResult(
        transcript=transcript,
        updates=results,
        applied_count=applied_count,
        interaction_id=interaction.id,
        contract=to_contract_view(last_record),
        reason=reason,
    )


@router.get("/{contract_id}/ai-interactions", response_model=list[AIInteractionView])
def get_ai_interactions(
    contract_id: UUID,
    contract_service: ContractService = Depends(get_contract_service),
) -> list[AIInteractionView]:
    try:
        records = contract_service.get_ai_interactions(contract_id)
    except ContractNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return [to_ai_interaction_view(item) for item in records]
