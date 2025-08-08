# tests/test_06_welcome_email.py
import pytest
from httpx import AsyncClient, ASGITransport
from uuid import uuid4
from app.main import app

@pytest.mark.asyncio
async def test_welcome_email_sent_on_complete(mocker):
    pid = uuid4()

    # initial + final profile reads in the route
    initial_profile = {
        "id": str(pid),
        "first_name": "Jane",
        "last_name": "Doe",
        "dob": "1995-05-01",
        "email": "newuser@example.com",
        "email_verified": True,
        "welcome_sent": False,
        "gender": None,
        "country": None,
        "preference": None,
        "height_cm": None,
        "religion": None,
        "pets": None,
        "smoking": None,
        "drinking": None,
        "kids": None,
        "goal": None,
        "description": None,
        "profile_picture_url": None,
        "gallery_urls": [],
        "embedding": None,
        "test_scores": None,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }
    final_profile = {**initial_profile, "updated_at": "2024-01-01T00:00:01"}

    mocker.patch(
        "app.services.profile_service.get_full_profile",
        side_effect=[initial_profile, final_profile],
    )

    mock_upsert = mocker.patch(
        "app.services.profile_service.simple_upsert_profile",
        return_value={"id": str(pid)}
    )

    mock_send_welcome = mocker.patch(
        "app.routers.profile_router.send_welcome_email",
        return_value=None,
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(f"/profiles/{pid}/complete")

    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == str(pid)
    assert body["email"] == "newuser@example.com"

    # Welcome email fired once with expected args
    mock_send_welcome.assert_called_once_with("newuser@example.com", "Jane")

    # Upsert was called twice: once to set is_complete, once to set welcome_sent
    payloads = [args[0] for (args, kwargs) in mock_upsert.call_args_list]

    assert any(p.get("is_complete") is True for p in payloads)
    assert any(p.get("welcome_sent") is True for p in payloads)
