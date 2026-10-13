"""Validated translation contracts and webhook response normalization for TransNova."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests
from pydantic import BaseModel, Field, field_validator


class TranslationRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20_000)
    target_language: str = Field(min_length=2, max_length=12)
    language_name: str = Field(min_length=1, max_length=80)
    source_language: str = Field(default="Auto-detect", max_length=80)
    context: str = Field(default="", max_length=500)

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Enter some text to translate.")
        return value


class TranslationResponse(BaseModel):
    translation: str = Field(min_length=1)
    target_language: str
    source_language: str = "Auto-detect"
    character_count: int = Field(ge=0)
    created_at: str


def extract_translation(payload: Any) -> str:
    """Normalize the supported n8n response shapes to one plain-text value."""
    current = payload
    if isinstance(current, list):
        if not current:
            raise ValueError("The translation workflow returned an empty list.")
        current = current[0]
    if isinstance(current, dict):
        for key in ("output", "translation", "translated_text", "text"):
            value = current.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        nested = current.get("data")
        if nested is not None:
            return extract_translation(nested)
    elif isinstance(current, str) and current.strip():
        return current.strip()
    raise ValueError("The workflow response did not contain a translation string.")


def request_translation(request_data: TranslationRequest, webhook_url: str) -> TranslationResponse:
    response = requests.post(
        webhook_url,
        json=request_data.model_dump(),
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        timeout=(5, 60),
    )
    response.raise_for_status()
    try:
        payload = response.json()
    except ValueError as exc:
        raise ValueError("The translation workflow returned invalid JSON.") from exc
    translated_text = extract_translation(payload)
    return TranslationResponse(
        translation=translated_text,
        target_language=request_data.language_name,
        source_language=request_data.source_language,
        character_count=len(translated_text),
        created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )
