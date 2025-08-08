import pytest

# All tests in this file use the `client` and `managed_user` fixtures.
pytestmark = pytest.mark.usefixtures("client", "managed_user")


def test_submit_questionnaire_and_generate_embedding(client, managed_user):
    """
    Tests submitting a questionnaire and verifies that test scores and a new
    embedding are generated and saved to the user's profile.
    """
    user_id = managed_user["id"]

    # 1. Get the initial state of the profile
    resp_initial = client.get(f"/profiles/{user_id}")
    assert resp_initial.status_code == 200
    initial_data = resp_initial.json()
    initial_embedding = initial_data.get("embedding")

    # In a fresh profile, embedding might be None or a list of zeros
    assert initial_data.get("test_scores") is None or initial_data.get("test_scores") == {}

    # 2. Submit the questionnaire
    # This submission is for the "mbti" questionnaire.
    submission_payload = {
        "user_id": str(user_id),
        "questionnaire_name": "mbti",
        "responses": ([0, 1, 0, 1, 0, 1, 0] * 10)  # Example responses
    }
    resp_submit = client.post("/questionnaires/submit", json=submission_payload)
    assert resp_submit.status_code == 201, f"Failed to submit questionnaire: {resp_submit.json()}"

    # 3. Get the final state and verify changes
    resp_final = client.get(f"/profiles/{user_id}")
    assert resp_final.status_code == 200
    final_data = resp_final.json()
    final_embedding = final_data.get("embedding")

    # Verify test scores were added
    assert "test_scores" in final_data
    assert final_data["test_scores"] is not None
    assert "MBTI Type" in final_data["test_scores"]

    # Verify embedding was generated and is different from the initial state
    assert final_embedding is not None
    assert initial_embedding != final_embedding
    # Check that the embedding is not just a list of zeros
    assert any(val != 0 for val in final_embedding)
