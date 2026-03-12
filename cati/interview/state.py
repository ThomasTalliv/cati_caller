"""InterviewState — shared data contract across all LangGraph nodes."""
from __future__ import annotations

import uuid
from typing import Any, Annotated
from operator import add

from pydantic import BaseModel, Field


class TranscriptTurnData(BaseModel):
    speaker: str  # "agent" | "respondent"
    text: str
    audio_offset_ms: int | None = None


class InterviewState(BaseModel):
    """Complete state of a live CATI interview session.

    This object is serialized to/from Redis keyed by call_id.
    All LangGraph nodes read from and write to this model.
    """

    # Identity
    call_id: uuid.UUID
    survey_id: uuid.UUID

    # Survey structure (loaded once at call start)
    questions: list[dict[str, Any]] = Field(default_factory=list)
    skip_rules: list[dict[str, Any]] = Field(default_factory=list)
    question_keys_in_order: list[str] = Field(default_factory=list)

    # Survey metadata
    intro_text: str | None = None
    outro_text: str | None = None
    language: str = "en"

    # Progress
    current_question_key: str | None = None
    responses: dict[str, Any] = Field(default_factory=dict)
    transcript: list[TranscriptTurnData] = Field(default_factory=list)

    # Control flags
    is_complete: bool = False
    was_refused: bool = False
    refusal_count: int = 0
    retry_count: int = 0

    # Last spoken / heard text (used between nodes)
    last_agent_text: str | None = None
    last_respondent_text: str | None = None

    # LangGraph routing signal
    next_node: str | None = None

    class Config:
        arbitrary_types_allowed = True

    def add_agent_turn(self, text: str, audio_offset_ms: int | None = None) -> None:
        self.transcript.append(
            TranscriptTurnData(speaker="agent", text=text, audio_offset_ms=audio_offset_ms)
        )
        self.last_agent_text = text

    def add_respondent_turn(self, text: str, audio_offset_ms: int | None = None) -> None:
        self.transcript.append(
            TranscriptTurnData(speaker="respondent", text=text, audio_offset_ms=audio_offset_ms)
        )
        self.last_respondent_text = text

    def record_response(self, question_key: str, value: Any) -> None:
        self.responses[question_key] = value

    def current_question_def(self) -> dict[str, Any] | None:
        if self.current_question_key is None:
            return None
        return next(
            (q for q in self.questions if q["question_key"] == self.current_question_key),
            None,
        )
