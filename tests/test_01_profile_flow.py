import pytest
from unittest.mock import patch, MagicMock
from uuid import UUID

def test_create_and_get_profile(client):
    user_id = UUID("123e4567-e89b-12d3-a456-426614174000")

    # Send imperial on input; backend should convert to height_cm=170 (~5'7")
    profile_input = {
        "first_name": "Test",
        "last_name": "User",
        "email": "test.user@example.com",
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
        ],
    }

    # What we expect stored/returned from DB after conversion
    stored_row = {
        "id": str(user_id),
        **{k: v for k, v in profile_input.items() if k not in ("height_feet", "height_inches")},
        "height_cm": 170,  # derived by service/model from 5'7"
    }

    with patch("app.services.profile_service.supabase") as mock_supabase:
        # Mock UPSERT
        mock_upsert_response = MagicMock()
        mock_upsert_response.data = [stored_row]
        mock_supabase.table.return_value.upsert.return_value.execute.return_value = mock_upsert_response

        # Mock GET (full profile)
        mock_get_response = MagicMock()
        mock_get_response.data = {
            **stored_row,
            # service returns ProfileOut including derived imperial + metadata
            "height_feet": 5,
            "height_inches": 7,
            "embedding": [0.1] * 128,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_get_response

        # Mock UPDATE (embedding) if your service updates it post-upsert
        mock_update_response = MagicMock()
        mock_update_response.data = [{**stored_row, "embedding": [0.1] * 128}]
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update_response

        # PUT
        resp_put = client.put(f"/profiles/{user_id}", json=profile_input)
        print(resp_put.status_code, resp_put.json())
        assert resp_put.status_code == 200
        data = resp_put.json()
        assert data["first_name"] == "Test"
        assert data["email"] == "test.user@example.com"
        assert data["country"] == "US"
        assert "embedding" in data
        # Height checks
        assert data["height_cm"] == 170
        assert data.get("height_feet") == 5
        assert data.get("height_inches") == 7
        # Gallery capped and echoed
        assert len(data.get("gallery_urls", [])) == 3

        # GET
        resp_get = client.get(f"/profiles/{user_id}")
        assert resp_get.status_code == 200
        data_get = resp_get.json()
        assert data_get["id"] == str(user_id)
        assert data_get["height_cm"] == 170
        assert data_get["height_feet"] == 5
        assert data_get["height_inches"] == 7
        assert data_get["country"] == "US"
        assert data_get["email"] == "test.user@example.com"

def test_get_profile_not_found(client):
    user_id = UUID("00000000-0000-0000-0000-000000000000")
    with patch("app.services.profile_service.supabase") as mock_supabase:
        mock_get_response = MagicMock()
        mock_get_response.data = None
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_get_response

        resp = client.get(f"/profiles/{user_id}")
        assert resp.status_code == 404
