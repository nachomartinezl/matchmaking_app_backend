# tests/test_07_verify_email_endpoint.py
import pytest
from httpx import AsyncClient, ASGITransport
from uuid import uuid4
import jwt
import os
from datetime import datetime, timedelta, timezone

from app.main import app
from app.services.email_service import EMAIL_VERIFY_SECRET

@pytest.fixture
def generate_token():
    def _generate_token(profile_id, secret=EMAIL_VERIFY_SECRET, expires_delta_days=1):
        """Generates a JWT token for email verification."""
        exp = datetime.now(timezone.utc) + timedelta(days=expires_delta_days)
        payload = {"profile_id": str(profile_id), "exp": exp}
        return jwt.encode(payload, secret, algorithm="HS256")
    return _generate_token

@pytest.mark.asyncio
async def test_verify_email_success(mocker, generate_token):
    profile_id = uuid4()
    token = generate_token(profile_id)

    mock_upsert = mocker.patch(
        "app.services.profile_service.simple_upsert_profile",
        return_value={"id": str(profile_id), "email_verified": True}
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get(f"/verify?token={token}")

    assert resp.status_code == 200
    assert resp.json()["message"] == "Email verified successfully"
    assert resp.json()["profile_id"] == str(profile_id)
    mock_upsert.assert_called_once_with({
        "id": str(profile_id),
        "email_verified": True
    })

@pytest.mark.asyncio
async def test_verify_email_expired_token(generate_token):
    profile_id = uuid4()
    # Token that expired yesterday
    token = generate_token(profile_id, expires_delta_days=-1)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get(f"/verify?token={token}")

    assert resp.status_code == 400
    assert resp.json()["detail"] == "Verification link has expired"

@pytest.mark.asyncio
async def test_verify_email_invalid_token():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/verify?token=invalidtoken")

    assert resp.status_code == 400
    assert resp.json()["detail"] == "Invalid verification token"

@pytest.mark.asyncio
async def test_verify_email_invalid_secret(generate_token):
    profile_id = uuid4()
    # Token signed with a different secret
    token = generate_token(profile_id, secret="wrong-secret")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get(f"/verify?token={token}")

    assert resp.status_code == 400
    assert resp.json()["detail"] == "Invalid verification token"
