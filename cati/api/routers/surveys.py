"""Survey CRUD endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from cati.api.dependencies import db_session, require_api_key
from cati.api.schemas.survey import (
    QuestionCreate,
    QuestionOut,
    QuestionReorder,
    SkipRuleCreate,
    SkipRuleOut,
    SurveyCreate,
    SurveyListItem,
    SurveyOut,
    SurveyUpdate,
)
from cati.db.repositories.survey_repo import SurveyRepository
from cati.survey.builder import QuestionDef, SkipRuleDef, SurveyBuilder
from cati.survey.validator import SurveyValidationError, validate_survey

router = APIRouter(prefix="/api/v1/surveys", tags=["surveys"], dependencies=[Depends(require_api_key)])


@router.post("", response_model=SurveyOut, status_code=status.HTTP_201_CREATED)
async def create_survey(
    body: SurveyCreate,
    session: AsyncSession = Depends(db_session),
) -> SurveyOut:
    builder = SurveyBuilder(body.name)
    builder.language(body.language)
    if body.description:
        builder.description(body.description)
    if body.intro_text:
        builder.intro(body.intro_text)
    if body.outro_text:
        builder.outro(body.outro_text)
    builder.max_duration(body.max_duration_s)
    if body.metadata:
        builder.meta(**body.metadata)

    for q in body.questions:
        builder.add_question(
            question_key=q.question_key,
            question_type=q.question_type,
            text=q.text,
            rephrasing=q.rephrasing,
            options=q.options,
            validation=q.validation,
            required=q.required,
            max_retries=q.max_retries,
        )
    for r in body.skip_rules:
        builder.add_skip_rule(
            source_key=r.source_question_key,
            condition_expr=r.condition_expr,
            target=r.target_question_key,
            priority=r.priority,
        )

    survey_def = builder.build()
    try:
        validate_survey(survey_def)
    except SurveyValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[str(e) for e in exc.errors],
        ) from exc

    repo = SurveyRepository(session)
    survey = await repo.create(survey_def)
    return SurveyOut.model_validate(survey)


@router.get("", response_model=list[SurveyListItem])
async def list_surveys(
    survey_status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(db_session),
) -> list[SurveyListItem]:
    repo = SurveyRepository(session)
    surveys = await repo.list(status=survey_status, limit=limit, offset=offset)
    return [
        SurveyListItem(
            id=s.id,
            name=s.name,
            status=s.status,
            language=s.language,
            created_at=s.created_at,
            question_count=len(s.questions) if s.questions else 0,
        )
        for s in surveys
    ]


@router.get("/{survey_id}", response_model=SurveyOut)
async def get_survey(
    survey_id: uuid.UUID,
    session: AsyncSession = Depends(db_session),
) -> SurveyOut:
    repo = SurveyRepository(session)
    survey = await repo.get(survey_id)
    if survey is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")
    return SurveyOut.model_validate(survey)


@router.put("/{survey_id}", response_model=SurveyOut)
async def update_survey(
    survey_id: uuid.UUID,
    body: SurveyUpdate,
    session: AsyncSession = Depends(db_session),
) -> SurveyOut:
    repo = SurveyRepository(session)
    updates = body.model_dump(exclude_none=True)
    survey = await repo.update(survey_id, updates)
    if survey is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")
    return SurveyOut.model_validate(survey)


@router.delete("/{survey_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_survey(
    survey_id: uuid.UUID,
    session: AsyncSession = Depends(db_session),
) -> None:
    repo = SurveyRepository(session)
    deleted = await repo.delete(survey_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")


@router.post("/{survey_id}/activate", response_model=SurveyOut)
async def activate_survey(
    survey_id: uuid.UUID,
    session: AsyncSession = Depends(db_session),
) -> SurveyOut:
    repo = SurveyRepository(session)
    survey = await repo.get(survey_id)
    if survey is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")
    if survey.status == "archived":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Cannot activate an archived survey"
        )
    updated = await repo.set_status(survey_id, "active")
    return SurveyOut.model_validate(updated)


# ── Questions ─────────────────────────────────────────────────────────────────

@router.post("/{survey_id}/questions", response_model=QuestionOut, status_code=status.HTTP_201_CREATED)
async def add_question(
    survey_id: uuid.UUID,
    body: QuestionCreate,
    session: AsyncSession = Depends(db_session),
) -> QuestionOut:
    repo = SurveyRepository(session)
    survey = await repo.get(survey_id)
    if survey is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")

    next_pos = max((q.position for q in survey.questions), default=0) + 1
    q_def = QuestionDef(
        question_key=body.question_key,
        question_type=body.question_type,
        text=body.text,
        position=next_pos,
        rephrasing=body.rephrasing,
        options=body.options,
        validation=body.validation,
        required=body.required,
        max_retries=body.max_retries,
    )
    question = await repo.add_question(survey_id, q_def)
    return QuestionOut.model_validate(question)


@router.put("/{survey_id}/questions/{question_id}", response_model=QuestionOut)
async def update_question(
    survey_id: uuid.UUID,
    question_id: uuid.UUID,
    body: QuestionCreate,
    session: AsyncSession = Depends(db_session),
) -> QuestionOut:
    repo = SurveyRepository(session)
    updates = body.model_dump(exclude_none=True)
    question = await repo.update_question(question_id, updates)
    if question is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    return QuestionOut.model_validate(question)


@router.delete("/{survey_id}/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(
    survey_id: uuid.UUID,
    question_id: uuid.UUID,
    session: AsyncSession = Depends(db_session),
) -> None:
    repo = SurveyRepository(session)
    deleted = await repo.delete_question(question_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")


@router.post("/{survey_id}/questions/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reorder_questions(
    survey_id: uuid.UUID,
    body: QuestionReorder,
    session: AsyncSession = Depends(db_session),
) -> None:
    repo = SurveyRepository(session)
    await repo.reorder_questions(survey_id, body.question_ids)


# ── Skip rules ────────────────────────────────────────────────────────────────

@router.post("/{survey_id}/skip-rules", response_model=SkipRuleOut, status_code=status.HTTP_201_CREATED)
async def add_skip_rule(
    survey_id: uuid.UUID,
    body: SkipRuleCreate,
    session: AsyncSession = Depends(db_session),
) -> SkipRuleOut:
    repo = SurveyRepository(session)
    r_def = SkipRuleDef(
        source_question_key=body.source_question_key,
        condition_expr=body.condition_expr,
        target_question_key=body.target_question_key,
        priority=body.priority,
    )
    try:
        rule = await repo.add_skip_rule(survey_id, r_def)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return SkipRuleOut.model_validate(rule)


@router.delete("/{survey_id}/skip-rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skip_rule(
    survey_id: uuid.UUID,
    rule_id: uuid.UUID,
    session: AsyncSession = Depends(db_session),
) -> None:
    repo = SurveyRepository(session)
    deleted = await repo.delete_skip_rule(rule_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skip rule not found")
