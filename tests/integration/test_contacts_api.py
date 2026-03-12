"""Integration tests for Contacts / DNC API."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_contact(client: AsyncClient):
    resp = await client.post(
        "/api/v1/contacts",
        json={"phone_number": "+15551234567", "name": "Alice"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["phone_number"] == "+15551234567"
    assert data["name"] == "Alice"
    assert data["do_not_call"] is False


@pytest.mark.asyncio
async def test_create_contact_invalid_phone(client: AsyncClient):
    resp = await client.post(
        "/api/v1/contacts",
        json={"phone_number": "notaphone"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_contacts(client: AsyncClient):
    await client.post("/api/v1/contacts", json={"phone_number": "+15551234567"})
    resp = await client.get("/api/v1/contacts")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_set_and_clear_dnc(client: AsyncClient):
    resp = await client.post("/api/v1/contacts", json={"phone_number": "+15559876543"})
    cid = resp.json()["id"]

    # Set DNC
    resp = await client.post(f"/api/v1/contacts/{cid}/do-not-call")
    assert resp.status_code == 204

    # Verify
    resp = await client.get(f"/api/v1/contacts/{cid}")
    assert resp.json()["do_not_call"] is True

    # Clear DNC
    resp = await client.delete(f"/api/v1/contacts/{cid}/do-not-call")
    assert resp.status_code == 204

    resp = await client.get(f"/api/v1/contacts/{cid}")
    assert resp.json()["do_not_call"] is False


@pytest.mark.asyncio
async def test_list_dnc_only(client: AsyncClient):
    await client.post("/api/v1/contacts", json={"phone_number": "+15551111111"})
    resp = await client.post(
        "/api/v1/contacts", json={"phone_number": "+15552222222", "do_not_call": True}
    )
    cid = resp.json()["id"]

    resp = await client.get("/api/v1/contacts?dnc_only=true")
    data = resp.json()
    assert all(c["do_not_call"] for c in data)
    ids = [c["id"] for c in data]
    assert cid in ids


@pytest.mark.asyncio
async def test_check_dnc_by_phone(client: AsyncClient):
    await client.post(
        "/api/v1/contacts",
        json={"phone_number": "+15553333333", "do_not_call": True},
    )
    resp = await client.post(
        "/api/v1/contacts/check-dnc",
        json={"phone_number": "+15553333333"},
    )
    assert resp.status_code == 200
    assert resp.json()["do_not_call"] is True


@pytest.mark.asyncio
async def test_check_dnc_clean_number(client: AsyncClient):
    resp = await client.post(
        "/api/v1/contacts/check-dnc",
        json={"phone_number": "+15554444444"},
    )
    assert resp.status_code == 200
    assert resp.json()["do_not_call"] is False


@pytest.mark.asyncio
async def test_update_contact(client: AsyncClient):
    resp = await client.post("/api/v1/contacts", json={"phone_number": "+15555555555"})
    cid = resp.json()["id"]
    resp = await client.patch(f"/api/v1/contacts/{cid}", json={"name": "Bob"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Bob"
