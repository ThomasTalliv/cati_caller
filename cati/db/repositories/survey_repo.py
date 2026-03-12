"""Repository for survey, question, and skip-rule persistence."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from cati.survey.builder import QuestionDef, SkipRuleDef, SurveyDef
from cati.survey.models import Question, SkipRule, Survey


class SurveyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, survey_def: SurveyDef) -> Survey:
        survey = Survey(
            id=survey_def.id,
            name=survey_def.name,
            description=survey_def.description,
            language=survey_def.language,
            intro_text=survey_def.intro_text,
            outro_text=survey_def.outro_text,
            max_duration_s=survey_def.max_duration_s,
            metadata_=survey_def.metadata,
            status="draft",
        )
        self._session.add(survey)
        await self._session.flush()

        for q_def in survey_def.questions:
            await self._add_question(survey.id, q_def)

        for r_def in survey_def.skip_rules:
            await self._add_skip_rule(survey.id, r_def)

        await self._session.commit()
        # Re-fetch with eager-loaded relationships
        return await self.get(survey.id)  # type: ignore[return-value]

    async def _add_question(self, survey_id: uuid.UUID, q_def: QuestionDef) -> Question:
        question = Question(
            id=q_def.id,
            survey_id=survey_id,
            position=q_def.position,
            question_key=q_def.question_key,
            question_type=q_def.question_type,
            text=q_def.text,
            rephrasing=q_def.rephrasing,
            options=q_def.options,
            validation=q_def.validation,
            required=q_def.required,
            max_retries=q_def.max_retries,
        )
        self._session.add(question)
        await self._session.flush()
        return question

    async def _add_skip_rule(self, survey_id: uuid.UUID, r_def: SkipRuleDef) -> SkipRule:
        # Resolve question keys to IDs
        source_q = await self._get_question_by_key(survey_id, r_def.source_question_key)
        target_q = (
            await self._get_question_by_key(survey_id, r_def.target_question_key)
            if r_def.target_question_key
            else None
        )
        rule = SkipRule(
            id=r_def.id,
            survey_id=survey_id,
            source_question_id=source_q.id,
            target_question_id=target_q.id if target_q else None,
            condition_expr=r_def.condition_expr,
            priority=r_def.priority,
        )
        self._session.add(rule)
        await self._session.flush()
        return rule

    async def _get_question_by_key(self, survey_id: uuid.UUID, key: str) -> Question:
        result = await self._session.execute(
            select(Question).where(
                Question.survey_id == survey_id, Question.question_key == key
            )
        )
        q = result.scalar_one_or_none()
        if q is None:
            raise ValueError(f"Question key {key!r} not found in survey {survey_id}")
        return q

    async def get(self, survey_id: uuid.UUID) -> Survey | None:
        result = await self._session.execute(
            select(Survey)
            .options(
                selectinload(Survey.questions),
                selectinload(Survey.skip_rules).selectinload(SkipRule.source_question),
                selectinload(Survey.skip_rules).selectinload(SkipRule.target_question),
            )
            .where(Survey.id == survey_id)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Survey]:
        query = (
            select(Survey)
            .options(selectinload(Survey.questions))
            .order_by(Survey.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if status:
            query = query.where(Survey.status == status)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def update(self, survey_id: uuid.UUID, updates: dict[str, Any]) -> Survey | None:
        survey = await self.get(survey_id)
        if survey is None:
            return None
        allowed = {"name", "description", "intro_text", "outro_text", "max_duration_s", "language"}
        for key, value in updates.items():
            if key in allowed:
                setattr(survey, key, value)
        await self._session.commit()
        return await self.get(survey_id)  # type: ignore[return-value]

    async def set_status(self, survey_id: uuid.UUID, status: str) -> Survey | None:
        survey = await self.get(survey_id)
        if survey is None:
            return None
        survey.status = status
        await self._session.commit()
        return await self.get(survey_id)

    async def delete(self, survey_id: uuid.UUID) -> bool:
        survey = await self.get(survey_id)
        if survey is None:
            return False
        survey.status = "archived"
        await self._session.commit()
        return True

    async def add_question(self, survey_id: uuid.UUID, q_def: QuestionDef) -> Question:
        question = await self._add_question(survey_id, q_def)
        await self._session.commit()
        return question

    async def update_question(
        self, question_id: uuid.UUID, updates: dict[str, Any]
    ) -> Question | None:
        result = await self._session.execute(
            select(Question).where(Question.id == question_id)
        )
        question = result.scalar_one_or_none()
        if question is None:
            return None
        allowed = {"text", "rephrasing", "options", "validation", "required", "max_retries"}
        for key, value in updates.items():
            if key in allowed:
                setattr(question, key, value)
        await self._session.commit()
        return question

    async def delete_question(self, question_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            select(Question).where(Question.id == question_id)
        )
        question = result.scalar_one_or_none()
        if question is None:
            return False
        await self._session.delete(question)
        await self._session.commit()
        return True

    async def reorder_questions(
        self, survey_id: uuid.UUID, ordered_ids: list[uuid.UUID]
    ) -> None:
        for pos, qid in enumerate(ordered_ids, start=1):
            result = await self._session.execute(
                select(Question).where(Question.id == qid, Question.survey_id == survey_id)
            )
            q = result.scalar_one_or_none()
            if q:
                q.position = pos
        await self._session.commit()

    async def add_skip_rule(self, survey_id: uuid.UUID, r_def: SkipRuleDef) -> SkipRule:
        rule = await self._add_skip_rule(survey_id, r_def)
        await self._session.commit()
        return rule

    async def delete_skip_rule(self, rule_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            select(SkipRule).where(SkipRule.id == rule_id)
        )
        rule = result.scalar_one_or_none()
        if rule is None:
            return False
        await self._session.delete(rule)
        await self._session.commit()
        return True
