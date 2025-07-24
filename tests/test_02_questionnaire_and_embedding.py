import pytest

def test_submit_questionnaire(client, test_user_factory):
    user = test_user_factory()
    user_id = user['id']
    client.put(f"/profiles/{user_id}", json={"first_name": "Quiz", "goal": "friends"})

    initial_profile_res = client.get(f"/profiles/{user_id}")
    initial_embedding = initial_profile_res.json()['embedding']

    mbti_submission = {
        "user_id": str(user_id),
        "questionnaire_name": "mbti",
        "responses": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1] * 7
    }
    response_submit = client.post("/questionnaires/submit", json=mbti_submission)
    
    assert response_submit.status_code == 201
    assert "rebuilt" in response_submit.json()['message']

    final_profile_res = client.get(f"/profiles/{user_id}")
    final_data = final_profile_res.json()

    assert "test_scores" in final_data
    assert "MBTI Type" in final_data['test_scores']
    
    final_embedding = final_data['embedding']
    assert initial_embedding != final_embedding
    assert any(val != 0 for val in final_embedding)