import pytest

# No more @pytest.mark.asyncio
# No more async def
def test_create_and_get_profile(client, test_user_factory):
    user = test_user_factory()
    user_id = user['id']
    
    profile_data = {
        "first_name": "Test",
        "last_name": "User",
        "goal": "relationship",
        "smoking": "never"
    }
    # No more await
    response_put = client.put(f"/profiles/{user_id}", json=profile_data)
    
    assert response_put.status_code == 200
    data = response_put.json()
    assert data['first_name'] == "Test"
    assert "embedding" in data
    
    response_get = client.get(f"/profiles/{user_id}")
    
    assert response_get.status_code == 200
    data_get = response_get.json()
    assert data_get['id'] == str(user_id)