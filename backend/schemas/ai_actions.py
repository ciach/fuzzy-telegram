from __future__ import annotations

import json
from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, Field, TypeAdapter


class UpdateFieldAction(BaseModel):
    action: Literal["update_field"]
    path: str
    value: Any


class RewriteClauseAction(BaseModel):
    action: Literal["rewrite_clause"]
    clause_id: str
    new_text: str


class NoAction(BaseModel):
    action: Literal["no_action"]
    reason: str


AIAction = Annotated[Union[UpdateFieldAction, RewriteClauseAction, NoAction], Field(discriminator="action")]
AI_ACTION_ADAPTER: TypeAdapter[AIAction] = TypeAdapter(AIAction)


class FieldPatch(BaseModel):
    path: str
    value: Any


class VoiceExtraction(BaseModel):
    updates: list[FieldPatch] = Field(default_factory=list)
    no_action_reason: str | None = None


VOICE_EXTRACTION_ADAPTER: TypeAdapter[VoiceExtraction] = TypeAdapter(VoiceExtraction)


def parse_ai_action(payload: dict[str, Any]) -> AIAction:
    return AI_ACTION_ADAPTER.validate_python(payload)


def parse_ai_action_json(payload: str) -> AIAction:
    parsed = json.loads(payload)
    return parse_ai_action(parsed)


def parse_voice_extraction_json(payload: str) -> VoiceExtraction:
    parsed = json.loads(payload)
    return VOICE_EXTRACTION_ADAPTER.validate_python(parsed)
