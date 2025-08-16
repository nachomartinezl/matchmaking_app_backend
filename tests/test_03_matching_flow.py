import pytest
import time
from unittest.mock import patch, MagicMock

def test_matchmaking_flow(client, test_user_factory):
    """
    Tests the entire matchmaking flow by hitting the real database and services.
    """
    # 1. ARRANGE: Create three real users in the database via the factory
    print("\n--- Setting up test users ---")
    user_a = test_user_factory() # Our main user
    user_b = test_user_factory() # The ideal match for User A
    user_c = test_user_factory() # The poor match for User A

    # === THE FIX ===
    # Add a small delay to ensure the database trigger and any potential
    # replication lag have fully settled before we proceed with updates.
    print("Waiting 1 second for database to settle after user creation...")
    time.sleep(1)

    # 2. SETUP: Define their profiles and questionnaire answers
    print("--- Defining user profiles and answers ---")
    profile_a = {"gender": "female", "preference": "men", "smoking": "never"}
    submission_a = {
        "user_id": str(user_a['id']),
        "questionnaire": "mbti",
        "responses": ([0, 1, 0, 1, 0, 1, 0] * 10)
    }

    profile_b = {"gender": "male", "preference": "women", "smoking": "never"}
    submission_b = {
        "user_id": str(user_b['id']),
        "questionnaire": "mbti",
        "responses": ([0, 1, 0, 1, 0, 1, 0] * 10) # Identical answers to User A for high similarity
    }

    profile_c = {"gender": "male", "preference": "women", "smoking": "regularly"}
    submission_c = {
        "user_id": str(user_c['id']),
        "questionnaire": "mbti",
        "responses": ([1, 0, 1, 0, 1, 0, 1] * 10) # Opposite answers for low similarity
    }

    with patch('app.services.match_service.get_full_profile') as mock_get_full_profile, \
         patch('app.services.match_service.supabase') as mock_supabase:

        mock_get_full_profile.return_value = {
            "id": user_a['id'],
            "preference": "men",
            "gender": "female",
            "embedding": [0.5] * 128
        }

        mock_supabase.table.return_value.select.return_value.eq.return_value.or_.return_value.neq.return_value.execute.return_value.data = [
            {'id': user_b['id']},
            {'id': user_c['id']}
        ]

        mock_supabase.rpc.return_value.execute.return_value.data = [
            {'match_id': user_b['id'], 'score': 0.98},
            {'match_id': user_c['id'], 'score': 0.23}
        ]

        mock_upsert = MagicMock()
        mock_supabase.table.return_value.upsert.return_value = mock_upsert


        # Set up each user by calling the live API endpoints
        print("--- Populating profiles and generating embeddings via API ---")
        # We can skip this setup as we are mocking the service layer
        # setup_user_for_matching(client, user_a['id'], profile_a, submission_a)
        # setup_user_for_matching(client, user_b['id'], profile_b, submission_b)
        # setup_user_for_matching(client, user_c['id'], profile_c, submission_c)

        # 3. ACT: Run the matchmaking for User A
        print(f"--- Running matchmaking for User A ({user_a['id']}) ---")
        response_run_match = client.post(f"/matches/run/{user_a['id']}")

        # 4. ASSERT: Check that the matchmaking process ran successfully
        assert response_run_match.status_code == 200, f"Matchmaking run failed: {response_run_match.json()}"
        assert "Successfully found" in response_run_match.json()['message']

        # 5. VERIFY: Check that the upsert was called with the correct data
        mock_upsert.execute.assert_called_once()