"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2026-03-12

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "surveys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("language", sa.String(10), nullable=False, server_default="en"),
        sa.Column("intro_text", sa.Text),
        sa.Column("outro_text", sa.Text),
        sa.Column("max_duration_s", sa.Integer, server_default="900"),
        sa.Column("metadata", postgresql.JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "survey_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("surveys.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer, nullable=False),
        sa.Column("question_key", sa.String(100), nullable=False),
        sa.Column("question_type", sa.String(30), nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("rephrasing", sa.Text),
        sa.Column("options", postgresql.JSONB),
        sa.Column("validation", postgresql.JSONB),
        sa.Column("required", sa.Boolean, server_default="true"),
        sa.Column("max_retries", sa.Integer, server_default="2"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("survey_id", "question_key", name="uq_questions_survey_key"),
    )

    op.create_table(
        "skip_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "survey_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("surveys.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "source_question_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("questions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "target_question_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("questions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("condition_expr", sa.Text, nullable=False),
        sa.Column("priority", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "contacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("phone_number", sa.String(20), nullable=False),
        sa.Column("name", sa.String(255)),
        sa.Column("metadata", postgresql.JSONB, server_default="{}"),
        sa.Column("do_not_call", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "call_batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "survey_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("surveys.id"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255)),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("scheduled_at", sa.DateTime(timezone=True)),
        sa.Column("config", postgresql.JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "calls",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "batch_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("call_batches.id"), nullable=True
        ),
        sa.Column(
            "survey_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("surveys.id"),
            nullable=False,
        ),
        sa.Column(
            "contact_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("contacts.id"), nullable=True
        ),
        sa.Column("phone_number", sa.String(20), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("signalwire_call_id", sa.String(255)),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("answered_at", sa.DateTime(timezone=True)),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.Column("duration_s", sa.Integer),
        sa.Column("attempt_number", sa.Integer, server_default="1"),
        sa.Column("failure_reason", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "responses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "call_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("calls.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "question_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("questions.id"), nullable=False
        ),
        sa.Column("question_key", sa.String(100), nullable=False),
        sa.Column("raw_transcript", sa.Text),
        sa.Column("parsed_value", postgresql.JSONB),
        sa.Column("is_refused", sa.Boolean, server_default="false"),
        sa.Column("is_skipped", sa.Boolean, server_default="false"),
        sa.Column("confidence", sa.Float),
        sa.Column("retries", sa.Integer, server_default="0"),
        sa.Column("asked_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "transcript_turns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "call_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("calls.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("speaker", sa.String(10), nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("audio_offset_ms", sa.Integer),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "analysis_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "call_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("calls.id"), nullable=True
        ),
        sa.Column(
            "survey_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("surveys.id"), nullable=True
        ),
        sa.Column("report_type", sa.String(30), nullable=False),
        sa.Column("llm_provider", sa.String(30)),
        sa.Column("llm_model", sa.String(50)),
        sa.Column("content", postgresql.JSONB, nullable=False),
        sa.Column("tokens_used", sa.Integer),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "exports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "survey_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("surveys.id"),
            nullable=False,
        ),
        sa.Column("format", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("file_path", sa.String(500)),
        sa.Column("external_url", sa.String(500)),
        sa.Column("call_count", sa.Integer),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )

    # Indexes
    op.create_index("idx_calls_survey_id", "calls", ["survey_id"])
    op.create_index("idx_calls_status", "calls", ["status"])
    op.create_index("idx_calls_batch_id", "calls", ["batch_id"])
    op.create_index("idx_responses_call_id", "responses", ["call_id"])
    op.create_index("idx_responses_question_key", "responses", ["question_key"])
    op.create_index("idx_transcript_turns_call_id", "transcript_turns", ["call_id"])
    op.create_index("idx_analysis_reports_survey_id", "analysis_reports", ["survey_id"])


def downgrade() -> None:
    op.drop_table("exports")
    op.drop_table("analysis_reports")
    op.drop_table("transcript_turns")
    op.drop_table("responses")
    op.drop_table("calls")
    op.drop_table("call_batches")
    op.drop_table("contacts")
    op.drop_table("skip_rules")
    op.drop_table("questions")
    op.drop_table("surveys")
