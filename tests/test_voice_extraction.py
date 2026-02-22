from __future__ import annotations

from backend.schemas.ai_actions import parse_voice_extraction_json


def test_parse_voice_extraction_json_valid_payload() -> None:
    payload = """
    {
      "updates": [
        {"path": "financial.total_price", "value": 45500},
        {"path": "financial.arras_amount", "value": 4550},
        {"path": "parties.buyers", "value": [{"full_name": "Buyer One", "id_number": "X123"}]}
      ],
      "no_action_reason": null
    }
    """
    parsed = parse_voice_extraction_json(payload)
    assert len(parsed.updates) == 3
    assert parsed.updates[0].path == "financial.total_price"
    assert parsed.updates[0].value == 45500


def test_parse_voice_extraction_json_empty_updates() -> None:
    payload = '{"updates":[],"no_action_reason":"empty_transcript"}'
    parsed = parse_voice_extraction_json(payload)
    assert parsed.updates == []
    assert parsed.no_action_reason == "empty_transcript"

