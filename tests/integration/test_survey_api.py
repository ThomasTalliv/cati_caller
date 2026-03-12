"""Integration tests for Survey CRUD API."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


SURVEY_PAYLOAD = {
    "name": "Test Survey",
    "language": "en",
    "intro_text": "Hello!",
    "outro_text": "Goodbye!",
    "questions": [
        {"question_key": "q1", "question_type": "yes_no", "text": "Do you like surveys?"},
    ],
}


@pytest.mark.asyncio
async def test_create_survey(client: AsyncClient):
    resp = await client.post("/api/v1/surveys", json=SURVEY_PAYLOAD)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test Survey"
    assert data["status"] == "draft"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_surveys_empty(client: AsyncClient):
    resp = await client.get("/api/v1/surveys")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_list_surveys_after_create(client: AsyncClient):
    await client.post("/api/v1/surveys", json=SURVEY_PAYLOAD)
    resp = await client.get("/api/v1/surveys")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_get_survey(client: AsyncClient):
    create_resp = await client.post("/api/v1/surveys", json=SURVEY_PAYLOAD)
    survey_id = create_resp.json()["id"]
    resp = await client.get(f"/api/v1/surveys/{survey_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == survey_id


@pytest.mark.asyncio
async def test_get_survey_not_found(client: AsyncClient):
    resp = await client.get("/api/v1/surveys/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_survey(client: AsyncClient):
    create_resp = await client.post("/api/v1/surveys", json=SURVEY_PAYLOAD)
    survey_id = create_resp.json()["id"]
    resp = await client.put(
        f"/api/v1/surveys/{survey_id}",
        json={"name": "Updated Survey"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Survey"


@pytest.mark.asyncio
async def test_add_question(client: AsyncClient):
    create_resp = await client.post("/api/v1/surveys", json=SURVEY_PAYLOAD)
    survey_id = create_resp.json()["id"]
    q_payload = {
        "question_key": "q2",
        "question_type": "open_ended",
        "text": "Any comments?",
    }
    resp = await client.post(f"/api/v1/surveys/{survey_id}/questions", json=q_payload)
    assert resp.status_code == 201
    assert resp.json()["question_key"] == "q2"


@pytest.mark.asyncio
async def test_add_skip_rule(client: AsyncClient):
    create_resp = await client.post("/api/v1/surveys", json=SURVEY_PAYLOAD)
    survey_id = create_resp.json()["id"]
    # Survey already has q1 from SURVEY_PAYLOAD; add q2 as the target
    await client.post(
        f"/api/v1/surveys/{survey_id}/questions",
        json={"question_key": "q2", "question_type": "open_ended", "text": "q2?"},
    )
    resp = await client.post(
        f"/api/v1/surveys/{survey_id}/skip-rules",
        json={
            "source_question_key": "q1",
            "condition_expr": "responses.q1 == 'no'",
            "target_question_key": None,
            "priority": 0,
        },
    )
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_activate_survey(client: AsyncClient):
    create_resp = await client.post("/api/v1/surveys", json=SURVEY_PAYLOAD)
    survey_id = create_resp.json()["id"]
    # Survey already has q1 from SURVEY_PAYLOAD; just activate directly
    resp = await client.post(f"/api/v1/surveys/{survey_id}/activate")
    assert resp.status_code == 200
    assert resp.json()["status"] == "active"


@pytest.mark.asyncio
async def test_require_api_key(client: AsyncClient):
    """Requests without the API key should be rejected."""
    from httpx import AsyncClient as RawClient, ASGITransport
    from cati.api.app import create_app

    app = create_app()
    async with RawClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        # No x-api-key header
    ) as ac:
        resp = await ac.get("/api/v1/surveys")
        assert resp.status_code == 422  # Missing required header


@pytest.mark.asyncio
async def test_wrong_api_key(client: AsyncClient):
    from httpx import AsyncClient as RawClient, ASGITransport
    from cati.api.app import create_app

    app = create_app()
    async with RawClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"x-api-key": "wrong-key"},
    ) as ac:
        resp = await ac.get("/api/v1/surveys")
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
