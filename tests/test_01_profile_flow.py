# tests/test_01_profile_flow.py
import pytest
from httpx import AsyncClient, ASGITransport
from uuid import UUID, uuid4
from unittest.mock import ANY

from app.main import app

@pytest.mark.asyncio
async def test_create_profile_and_send_verification_email(mocker):
    # mock DB upsert so we don't hit Supabase
    mocker.patch(
        "app.services.profile_service.get_profile_by_email",
        return_value=None
    )
    mocker.patch(
        "app.services.profile_service.simple_upsert_profile",
        return_value={"id": str(uuid4())}
    )
    # patch where it's USED (router), not defined
    mock_send = mocker.patch(
        "app.routers.profile_router.send_verification_email",
        return_value=None,
    )

    payload = {
        "first_name": "Test",
        "last_name": "User",
        "dob": "1990-01-01",
        "email": "test.user@example.com",
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post("/profiles", json=payload)

    assert resp.status_code == 200
    data = resp.json()
    assert "id" in data
    UUID(data["id"])  # valid UUID
    mock_send.assert_called_once_with(email="test.user@example.com", profile_id=ANY)

@pytest.mark.asyncio
async def test_update_profile_full_data(mocker):
    # fake ids & timestamps for ProfileOut validation
    pid = uuid4()
    created = "2024-01-01T00:00:00"
    updated = "2024-01-01T00:00:00"

    # what the DB should return after upsert
    upsert_row = {
        "id": str(pid),
        "first_name": "Test",
        "last_name": "User",
        "dob": "1990-01-01",
        "email": "test.user@example.com",
        "gender": "female",
        "country": "US",
        "preference": "men",
        "height_cm": 170,  # derived from 5'7"
        "religion": "atheism",
        "pets": "none",
        "smoking": "never",
        "drinking": "sometimes",
        "kids": "not_sure",
        "goal": "relationship",
        "description": "Just a test user.",
        "profile_picture_url": "https://example.com/profile.jpg",
        "gallery_urls": [
            "https://example.com/1.jpg",
            "https://example.com/2.jpg",
            "https://example.com/3.jpg",
            "https://example.com/4.jpg",
        ],
        "embedding": None,
        "test_scores": None,
        "created_at": created,
        "updated_at": updated,
    }

    # simple_upsert_profile returns the row we pass back
    mocker.patch(
        "app.services.profile_service.simple_upsert_profile",
        return_value=upsert_row,
    )

    payload = {
        "first_name": "Test",
        "last_name": "User",
        "goal": "relationship",
        "smoking": "never",
        "dob": "1990-01-01",
        "gender": "female",
        "country": "US",
        "preference": "men",
        "height_feet": 5,
        "height_inches": 7,
        "religion": "atheism",
        "pets": "none",
        "drinking": "sometimes",
        "kids": "not_sure",
        "description": "Just a test user.",
        "profile_picture_url": "https://example.com/profile.jpg",
        "gallery_urls": [
            "https://example.com/1.jpg",
            "https://example.com/2.jpg",
            "https://example.com/3.jpg",
            "https://example.com/4.jpg",
        ],
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 🔁 use PATCH (you removed PUT)
        resp = await ac.patch(f"/profiles/{pid}", json=payload)

    assert resp.status_code == 200
    data = resp.json()
    assert data["first_name"] == "Test"
    assert data["country"] == "US"
    assert data["height_cm"] == 170
    # ProfileOut derives these from height_cm on response
    assert data["height_feet"] == 5
    assert data["height_inches"] == 7
    # limit is <= 6; we sent 4 so it should echo back 4
    assert len(data["gallery_urls"]) == 4
