import pytest
from httpx import AsyncClient, ASGITransport
from uuid import UUID
from unittest.mock import ANY
from app.main import app


@pytest.mark.asyncio
async def test_start_profile_success(mocker):
    # Patch DB upsert
    mocker.patch(
        "app.services.profile_service.get_profile_by_email",
        return_value=None
    )
    mocker.patch(
        "app.services.profile_service.simple_upsert_profile",
        return_value={"id": "1234"}
    )
    # Patch email send where it's imported in the router
    mock_send_email = mocker.patch(
        "app.routers.profile_router.send_verification_email",
        return_value=None
    )

    payload = {
        "first_name": "Jane",
        "last_name": "Doe",
        "dob": "1995-05-01",
        "email": "jane@example.com"
    }

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        resp = await ac.post("/profiles", json=payload)

    assert resp.status_code == 200
    body = resp.json()
    assert "id" in body
    UUID(body["id"])  # Valid UUID

    mock_send_email.assert_called_once_with(
        email="jane@example.com",
        profile_id=ANY
    )


@pytest.mark.asyncio
async def test_start_profile_missing_fields():
    payload = {
        "first_name": "Jane",
        "dob": "1995-05-01",
        # missing last_name and email
    }

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        resp = await ac.post("/profiles", json=payload)

    assert resp.status_code == 400
    assert "Missing required fields" in resp.json()["detail"]
