from __future__ import annotations

import io
import json
from typing import Any

from backend.core.config import get_settings
from backend.schemas.ai_actions import (
    AIAction,
    NoAction,
    UpdateFieldAction,
    VoiceExtraction,
    parse_ai_action_json,
    parse_voice_extraction_json,
)
from backend.schemas.contract_schema import ContractSchema

try:
    from openai import AsyncOpenAI
except Exception:  # pragma: no cover
    AsyncOpenAI = None  # type: ignore[assignment]


SYSTEM_PROMPT = """
You are a legal assistant restricted to Arras Penitenciales contracts in Catalonia.
Never return prose.
Return one JSON object only with one action:
- {"action":"update_field","path":"...","value":...}
- {"action":"rewrite_clause","clause_id":"...","new_text":"..."}
- {"action":"no_action","reason":"..."}
If uncertain, return no_action.
""".strip()

VOICE_SYSTEM_PROMPT = """
You extract structured field updates for a Catalonia arras contract from a voice transcript.
Never invent values.
Use only these output keys:
- updates: array of {path, value}
- no_action_reason: optional string

Allowed paths include:
metadata.location
metadata.date
metadata.language
parties.sellers
parties.buyers
property.address
property.registry
property.cargas
property.ibi
financial.total_price
financial.arras_amount
financial.deadline

For parties.sellers and parties.buyers, value must be an array of objects:
{ "full_name": "...", "id_number": "..." | null }

If transcript is unclear or empty, return no_action_reason and empty updates.
""".strip()

AI_ACTION_JSON_SCHEMA: dict[str, Any] = {
    "name": "arras_action",
    "strict": True,
    "schema": {
        "type": "object",
        "oneOf": [
            {
                "type": "object",
                "properties": {
                    "action": {"const": "update_field"},
                    "path": {"type": "string"},
                    "value": {},
                },
                "required": ["action", "path", "value"],
                "additionalProperties": False,
            },
            {
                "type": "object",
                "properties": {
                    "action": {"const": "rewrite_clause"},
                    "clause_id": {"type": "string"},
                    "new_text": {"type": "string"},
                },
                "required": ["action", "clause_id", "new_text"],
                "additionalProperties": False,
            },
            {
                "type": "object",
                "properties": {
                    "action": {"const": "no_action"},
                    "reason": {"type": "string"},
                },
                "required": ["action", "reason"],
                "additionalProperties": False,
            },
        ],
    },
}

VOICE_EXTRACTION_JSON_SCHEMA: dict[str, Any] = {
    "name": "voice_arras_extraction",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "updates": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "value": {},
                    },
                    "required": ["path", "value"],
                    "additionalProperties": False,
                },
            },
            "no_action_reason": {"type": "string"},
        },
        "required": ["updates"],
        "additionalProperties": False,
    },
}


class AIService:
    def __init__(self) -> None:
        settings = get_settings()
        self._model = settings.openai_model
        self._transcription_model = settings.openai_transcription_model
        self._client = None
        if settings.openai_api_key and AsyncOpenAI is not None:
            self._client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def propose_action(self, *, user_message: str, contract: ContractSchema) -> tuple[AIAction, str]:
        if self._client is None:
            action = NoAction(action="no_action", reason="openai_not_configured")
            return action, action.model_dump_json()

        user_payload = {
            "message": user_message,
            "contract": contract.model_dump(mode="json"),
        }
        try:
            completion = await self._client.chat.completions.create(
                model=self._model,
                temperature=0,
                max_tokens=300,
                response_format={"type": "json_schema", "json_schema": AI_ACTION_JSON_SCHEMA},
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": json.dumps(user_payload)},
                ],
            )
            raw_response = completion.choices[0].message.content or '{"action":"no_action","reason":"empty_response"}'
            return self._parse_action(raw_response)
        except Exception:
            action = NoAction(action="no_action", reason="ai_provider_error")
            return action, action.model_dump_json()

    def _parse_action(self, raw_response: str) -> tuple[AIAction, str]:
        try:
            normalized = _extract_json_payload(raw_response)
            action = parse_ai_action_json(normalized)
            return action, raw_response
        except Exception:
            action = NoAction(action="no_action", reason="invalid_ai_output")
            return action, raw_response

    @staticmethod
    def parse_action_payload(payload: dict[str, Any]) -> AIAction:
        return parse_ai_action_json(json.dumps(payload))

    async def transcribe_audio(
        self,
        *,
        audio_bytes: bytes,
        filename: str = "voice.webm",
        language: str = "es",
    ) -> str:
        if self._client is None:
            return ""
        if not audio_bytes:
            return ""

        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = filename
        try:
            transcript = await self._client.audio.transcriptions.create(
                model=self._transcription_model,
                file=audio_file,
                language=language,
            )
            text = getattr(transcript, "text", "")
            return (text or "").strip()
        except Exception:
            return ""

    async def propose_updates_from_transcript(
        self,
        *,
        transcript: str,
        contract: ContractSchema,
    ) -> tuple[list[UpdateFieldAction], str, str | None]:
        if self._client is None:
            return [], '{"updates":[],"no_action_reason":"openai_not_configured"}', "openai_not_configured"

        if not transcript.strip():
            return [], '{"updates":[],"no_action_reason":"empty_transcript"}', "empty_transcript"

        user_payload = {
            "transcript": transcript,
            "contract": contract.model_dump(mode="json"),
        }
        try:
            completion = await self._client.chat.completions.create(
                model=self._model,
                temperature=0,
                max_tokens=600,
                response_format={"type": "json_schema", "json_schema": VOICE_EXTRACTION_JSON_SCHEMA},
                messages=[
                    {"role": "system", "content": VOICE_SYSTEM_PROMPT},
                    {"role": "user", "content": json.dumps(user_payload)},
                ],
            )
            raw_response = completion.choices[0].message.content or '{"updates":[],"no_action_reason":"empty_response"}'
            extraction, reason = self._parse_voice_extraction(raw_response)
            updates = [
                UpdateFieldAction(action="update_field", path=item.path, value=item.value)
                for item in extraction.updates
            ]
            return updates, raw_response, reason
        except Exception:
            return [], '{"updates":[],"no_action_reason":"ai_provider_error"}', "ai_provider_error"

    def _parse_voice_extraction(self, raw_response: str) -> tuple[VoiceExtraction, str | None]:
        try:
            normalized = _extract_json_payload(raw_response)
            extraction = parse_voice_extraction_json(normalized)
            return extraction, extraction.no_action_reason
        except Exception:
            extraction = VoiceExtraction(updates=[], no_action_reason="invalid_ai_output")
            return extraction, extraction.no_action_reason


def _extract_json_payload(raw: str) -> str:
    stripped = raw.strip()
    if stripped.startswith("```"):
        parts = [line for line in stripped.splitlines() if not line.strip().startswith("```")]
        stripped = "\n".join(parts).strip()
    return stripped
