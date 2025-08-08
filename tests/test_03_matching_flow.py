import pytest
import time

# A helper function to update a profile and submit a questionnaire for a user
def setup_user_for_matching(client, user_id, profile_data, questionnaire_submission):
    """A helper to perform the full setup for a single user."""
    # Update their profile with specific test data
    # Note: The user and a basic profile are already created by the factory
    res_patch = client.patch(f"/profiles/{user_id}", json=profile_data)
    assert res_patch.status_code == 200, f"Failed to patch profile for {user_id}: {res_patch.json()}"
    
    # Have them submit the questionnaire to generate the full embedding
    res_post = client.post("/questionnaires/submit", json=questionnaire_submission)
    assert res_post.status_code == 201, f"Failed to submit questionnaire for {user_id}: {res_post.json()}"


def test_matchmaking_flow(client, managed_user_factory):
    """
    Tests the entire matchmaking flow using managed users for setup and teardown.
    """
    # 1. ARRANGE: Create three managed users using the factory
    print("\n--- Setting up test users ---")
    user_a = managed_user_factory() # Our main user
    user_b = managed_user_factory() # The ideal match for User A
    user_c = managed_user_factory() # The poor match for User A

    # Add a small delay to ensure database operations settle
    print("Waiting 1 second for database to settle after user creation...")
    time.sleep(1) 

    # 2. SETUP: Define their specific profiles and questionnaire answers
    print("--- Defining user profiles and answers ---")
    profile_a = {"gender": "female", "preference": "men", "smoking": "never"}
    submission_a = {
        "user_id": str(user_a['id']),
        "questionnaire_name": "mbti",
        "responses": ([0, 1, 0, 1, 0, 1, 0] * 10)
    }

    profile_b = {"gender": "male", "preference": "women", "smoking": "never"}
    submission_b = {
        "user_id": str(user_b['id']),
        "questionnaire_name": "mbti",
        "responses": ([0, 1, 0, 1, 0, 1, 0] * 10) # Identical answers
    }
    
    profile_c = {"gender": "male", "preference": "women", "smoking": "regularly"}
    submission_c = {
        "user_id": str(user_c['id']),
        "questionnaire_name": "mbti",
        "responses": ([1, 0, 1, 0, 1, 0, 1] * 10) # Opposite answers
    }
    
    # Set up each user by calling the live API endpoints
    print("--- Populating profiles and generating embeddings via API ---")
    setup_user_for_matching(client, user_a['id'], profile_a, submission_a)
    setup_user_for_matching(client, user_b['id'], profile_b, submission_b)
    setup_user_for_matching(client, user_c['id'], profile_c, submission_c)

    # 3. ACT: Run the matchmaking for User A
    print(f"--- Running matchmaking for User A ({user_a['id']}) ---")
    response_run_match = client.post(f"/matches/run/{user_a['id']}")
    
    # 4. ASSERT: Check that the matchmaking process ran successfully
    assert response_run_match.status_code == 200, f"Matchmaking run failed: {response_run_match.json()}"
    assert "Successfully found" in response_run_match.json()['message']

    # 5. VERIFY: Check the resulting matches in the real database
    print("--- Verifying matches in database ---")
    from app.database import supabase
    response_matches = supabase.table("matches").select("*, match_id(id)").eq("user_id", user_a['id']).execute()
    
    assert response_matches.data, "No matches were created in the database."
    assert len(response_matches.data) == 2, f"Expected 2 matches, but found {len(response_matches.data)}"
    
    match_scores = {match['match_id']: match['score'] for match in response_matches.data}

    assert str(user_b['id']) in match_scores, "User B was not found in the matches."
    assert str(user_c['id']) in match_scores, "User C was not found in the matches."
    
    score_b = match_scores[str(user_b['id'])]
    score_c = match_scores[str(user_c['id'])]
    
    print(f"Match score for similar user (B): {score_b}")
    print(f"Match score for different user (C): {score_c}")
    
    assert score_b > score_c, f"Score for similar user B ({score_b}) was not higher than for different user C ({score_c})."
    assert score_b > 0.95, f"Score for similar user B ({score_b}) was unexpectedly low."