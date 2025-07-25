import pytest
from unittest.mock import patch, MagicMock
from uuid import UUID

def test_submit_questionnaire(client, test_user_factory):
    user = test_user_factory()
    user_id = user['id']

    profile_data = {
        "first_name": "Quiz",
        "last_name": "User",
        "goal": "friends",
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

    with patch('app.services.profile_service.get_full_profile') as mock_get_full_profile, \
         patch('app.services.questionnaire_service.supabase') as mock_supabase_in_q_service, \
         patch('app.services.profile_service.supabase') as mock_supabase_in_p_service:

        # 1. Define a generic successful Supabase response
        mock_db_success = MagicMock()
        mock_db_success.data = [{}] # A non-empty list signifies success to our app code

        # 2. Configure both mocks to behave identically
        for mock_supabase in [mock_supabase_in_q_service, mock_supabase_in_p_service]:
            mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_db_success
            mock_supabase.table.return_value.upsert.return_value.execute.return_value = mock_db_success
            mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_db_success
            mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_db_success

        # 3. Define state snapshots
        initial_profile = {
            "id": user_id, **profile_data,
            "embedding": [0.0] * 128,
            "created_at": "2024-01-01T00:00:00", "updated_at": "2024-01-01T00:00:00",
            "test_scores": {}
        }
        profile_after_q = {
            **initial_profile,
            "test_scores": {"MBTI Type": "INFP"},
            "embedding": [0.1] * 128,
        }

        # 4. Implement sequential mocking for get_full_profile
        mock_get_full_profile.side_effect = [
            initial_profile, # Call inside PUT /profiles
            initial_profile, # Call inside GET /profiles
            initial_profile, # Call inside POST /questionnaires/submit
                profile_after_q, # Call inside profile_service.update_test_scores_and_rebuild_embedding
                profile_after_q,  # Call inside final GET /profiles
                profile_after_q
        ]

        # --- Test Execution ---
        # 1. Create the initial profile
        response_put = client.put(f"/profiles/{user_id}", json=profile_data)
        assert response_put.status_code == 200

        # 2. Get the initial state
        initial_profile_res = client.get(f"/profiles/{user_id}")
        initial_data = initial_profile_res.json()
        initial_embedding = initial_data['embedding']
        assert initial_data['test_scores'] == {}

        # 3. Submit the questionnaire
        mbti_submission = {
            "user_id": str(user_id),
            "questionnaire": "mbti",
            "responses": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1] * 7
        }
        response_submit = client.post("/questionnaires/submit", json=mbti_submission)
        assert response_submit.status_code == 201

        # 4. Get the final state and verify changes
        final_profile_res = client.get(f"/profiles/{user_id}")
        final_data = final_profile_res.json()

        assert "test_scores" in final_data
        assert final_data['test_scores'] is not None
        assert "MBTI Type" in final_data['test_scores']

        final_embedding = final_data['embedding']
        assert initial_embedding != final_embedding
        assert any(val != 0 for val in final_embedding)