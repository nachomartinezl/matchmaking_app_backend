import pytest
from unittest.mock import patch, MagicMock
from uuid import UUID
from app.models import RelationshipGoal, SmokingHabit

def test_create_and_get_profile(client):
    user_id = UUID("123e4567-e89b-12d3-a456-426614174000")

    profile_data = {
        "first_name": "Test",
        "last_name": "User",
        "goal": "relationship",
            "smoking": "never",
            "dob": "1990-01-01",
            "gender": "female",
            "country": "US",
            "preference": "men",
            "height_cm": 170,
            "religion": "atheism",
            "pets": "none",
            "drinking": "sometimes",
            "kids": "not_yet",
            "marital_status": "single",
            "description": "Just a test user.",
            "profile_picture_url": "https://example.com/profile.jpg"
    }

    # Mock the database calls
    with patch('app.services.profile_service.supabase') as mock_supabase:
        # Mock for upsert
        mock_upsert_response = MagicMock()
        mock_upsert_response.data = [{"id": str(user_id), **profile_data}]
        mock_supabase.table.return_value.upsert.return_value.execute.return_value = mock_upsert_response

        # Mock for get_full_profile
        mock_get_response = MagicMock()
        mock_get_response.data = {"id": str(user_id), **profile_data, "embedding": [0.1] * 128, "created_at": "2024-01-01T00:00:00", "updated_at": "2024-01-01T00:00:00"}
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_get_response

        # Mock for update (embedding)
        mock_update_response = MagicMock()
        mock_update_response.data = [{"id": str(user_id), **profile_data, "embedding": [0.1] * 128}]
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update_response

        # Test PUT request
        response_put = client.put(f"/profiles/{user_id}", json=profile_data)

        print(response_put.json())
        assert response_put.status_code == 200
        data = response_put.json()
        assert data['first_name'] == "Test"
        assert "embedding" in data

        # Test GET request
        response_get = client.get(f"/profiles/{user_id}")

        assert response_get.status_code == 200
        data_get = response_get.json()
        assert data_get['id'] == str(user_id)

def test_get_profile_not_found(client):
    user_id = UUID("00000000-0000-0000-0000-000000000000")
    with patch('app.services.profile_service.supabase') as mock_supabase:
        mock_get_response = MagicMock()
        mock_get_response.data = None
        mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_get_response

        response = client.get(f"/profiles/{user_id}")
        assert response.status_code == 404