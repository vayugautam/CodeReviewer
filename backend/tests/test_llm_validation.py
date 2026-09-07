"""The LLM boundary must reject invalid data before it reaches the API."""

import json

import pytest
from pydantic import ValidationError

from app.services import llm_service
from app.schemas.diff import ChangedFile
from app.services.llm_service import LLMServiceError, _parse_llm_response, review_with_llm


def payload(**overrides):
    value = {
        "summary": "No evidence of a reasoning-level issue.",
        "overall_status": "approve",
        "findings": [],
    }
    value.update(overrides)
    return json.dumps(value)


def test_accepts_empty_findings_as_a_clean_review():
    assert _parse_llm_response(payload()).findings == []


def test_rejects_malformed_json():
    with pytest.raises(json.JSONDecodeError):
        _parse_llm_response("not json")


def test_rejects_missing_required_fields():
    with pytest.raises(ValidationError):
        _parse_llm_response('{"summary": "only this"}')


def test_rejects_invalid_enum_and_wrong_scalar_types():
    with pytest.raises(ValidationError):
        _parse_llm_response(payload(overall_status="ship_it"))
    with pytest.raises(ValidationError):
        _parse_llm_response(payload(summary=123))


def test_rejects_extra_fields_and_non_integer_line_numbers():
    invalid = {
        "summary": "Possible issue.",
        "overall_status": "review",
        "findings": [{
            "severity": "medium", "category": "bug", "file": "a.py",
            "line": "4", "message": "Potential issue.", "suggestion": "Check it.",
        }],
        "unexpected": True,
    }
    with pytest.raises(ValidationError):
        _parse_llm_response(json.dumps(invalid))


class Response:
    def __init__(self, text): self.text = text


class Chat:
    def __init__(self, corrected): self.corrected, self.calls = corrected, 0
    def send_message(self, _):
        self.calls += 1
        return Response(self.corrected if self.calls == 2 else "ignored")


class Model:
    def __init__(self, first, corrected, **_): self.first, self.chat = first, Chat(corrected)
    def generate_content(self, *_ , **__): return Response(self.first)
    def start_chat(self): return self.chat


class FakeGenAI:
    def __init__(self, first, corrected): self.first, self.corrected = first, corrected
    def configure(self, **_): pass
    def GenerativeModel(self, **kwargs): return Model(self.first, self.corrected, **kwargs)


def test_validation_failure_gets_one_successful_correction(monkeypatch):
    monkeypatch.setattr(llm_service.settings, "gemini_api_key", "test-key")
    monkeypatch.setattr(llm_service, "genai", FakeGenAI("not json", payload()))
    review = review_with_llm("title", "", [ChangedFile("a.py", "modified", 0, 0)], [])
    assert review.overall_status.value == "approve"


def test_retry_failure_returns_controlled_error(monkeypatch):
    monkeypatch.setattr(llm_service.settings, "gemini_api_key", "test-key")
    monkeypatch.setattr(llm_service, "genai", FakeGenAI("not json", "still not json"))
    with pytest.raises(LLMServiceError, match="after 2 attempts"):
        review_with_llm("title", "", [ChangedFile("a.py", "modified", 0, 0)], [])
