# tests/test_05_email_verification_flow.py
import pytest
from httpx import AsyncClient, ASGITransport
from uuid import UUID
import uuid  # <-- add this
from app.main import app

@pytest.mark.asyncio
async def test_verification_email_sent(mocker):
    # Mock the two database functions that get called
    mocker.patch(
        "app.services.profile_service.get_profile_by_email",
        return_value=None  # Simulate user not existing
    )
    mocker.patch(
        "app.services.profile_service.simple_upsert_profile",
        return_value={"id": str(uuid.uuid4())}  # Simulate successful insert
    )
    mock_send_email = mocker.patch(
        "app.services.email_service._send_email",
        return_value=None
    )

    unique_email = f"jane+{uuid.uuid4().hex}@example.com"  # <-- unique each run
    payload = {
        "first_name": "Jane",
        "last_name": "Doe",
        "dob": "1995-05-01",
        "email": unique_email,
    }

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        resp = await ac.post("/profiles", json=payload)

    assert resp.status_code == 200
    body = resp.json()
    assert "id" in body
    UUID(body["id"])

    # _send_email called once with our email + verification content
    assert mock_send_email.call_count == 1
    args, _ = mock_send_email.call_args
    assert args[0] == unique_email
    assert "Verify your email" in args[1]
    assert "Verify Email" in args[2]
