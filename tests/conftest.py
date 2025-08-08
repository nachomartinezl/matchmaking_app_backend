import sys
import os

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from uuid import uuid4
from fastapi.testclient import TestClient # <--- IMPORT TestClient

from app.main import app
from app.database import supabase

# Fixture to provide a test client for making API calls
@pytest.fixture(scope="module")
def client():
    # The TestClient makes synchronous-style requests to your async app
    with TestClient(app) as c:
        yield c

from unittest.mock import patch, MagicMock

# The most important fixture: A factory to create and clean up test users
@pytest.fixture(scope="function")
def test_user_factory():
    created_users = []

    def _create_user():
        test_email = f"test-user-{uuid4()}@example.com"
        
        # Mock the user object that would be returned by Supabase
        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.email = test_email

        # Mock the sign_up response
        mock_sign_up_response = MagicMock()
        mock_sign_up_response.user = mock_user
        
        with patch('app.database.supabase.auth.sign_up', return_value=mock_sign_up_response):
            response = supabase.auth.sign_up({
                "email": test_email,
                "password": "password123",
            })

            if response.user is None:
                raise Exception("Failed to create test user in Supabase Auth.")

            new_user = response.user
            created_users.append(new_user.id)

            print(f"\nCREATED Test User: {new_user.id} ({new_user.email})")
            return {"id": str(new_user.id), "email": new_user.email}

    yield _create_user

    # --- Teardown ---
    print(f"\nTEARDOWN: Deleting {len(created_users)} test users...")
    # In a mocked environment, we don't need to call the real delete_user
    # but we can simulate it for logging purposes.
    for user_id in created_users:
        print(f"DELETED Test User: {user_id}")


@pytest.fixture(scope="function")
def managed_user(client, test_user_factory):
    """
    A fixture that creates a user and a corresponding profile, and then
    cleans up all related database records on teardown.
    """
    # 1. ARRANGE: Create a user with the factory
    user = test_user_factory()
    user_id = user["id"]

    # 2. ARRANGE: Create a basic profile for them via the API
    profile_data = {
        "first_name": "Managed",
        "last_name": "User",
        "dob": "1999-01-19",
        "email": user["email"],
    }
    # This POST hits the real DB via the API because we don't mock it here
    response = client.post("/profiles", json=profile_data)
    assert response.status_code == 200, f"Failed to create profile for managed user: {response.json()}"

    # 3. YIELD: Provide the user details to the test
    yield user

    # 4. TEARDOWN: Clean up all database records for this user
    print(f"\nTEARDOWN: Deleting data for user {user_id}")
    try:
        # Use the real supabase client to delete from all relevant tables
        supabase.table("matches").delete().eq("user_id", user_id).execute()
        supabase.table("matches").delete().eq("match_id", user_id).execute()
        supabase.table("questionnaire_responses").delete().eq("user_id", user_id).execute()
        supabase.table("profiles").delete().eq("id", user_id).execute()
        print(f"Cleaned up data for user {user_id}")
    except Exception as e:
        print(f"Error during teardown for user {user_id}: {e}")


@pytest.fixture(scope="function")
def managed_user_factory(client, test_user_factory):
    """
    A factory fixture that creates multiple users with profiles and cleans
    up all of them on teardown.
    """
    created_user_ids = []

    def _create_managed_user():
        user = test_user_factory()
        user_id = user["id"]

        profile_data = {
            "first_name": "FactoryManaged",
            "last_name": "User",
            "dob": "1998-01-01",
            "email": user["email"],
        }
        response = client.post("/profiles", json=profile_data)
        assert response.status_code == 200, f"Failed to create profile for factory user: {response.json()}"

        created_user_ids.append(user_id)
        return user

    yield _create_managed_user

    # --- Teardown ---
    print(f"\nTEARDOWN: Deleting data for {len(created_user_ids)} factory-managed users...")
    for user_id in created_user_ids:
        try:
            supabase.table("matches").delete().eq("user_id", user_id).execute()
            supabase.table("matches").delete().eq("match_id", user_id).execute()
            supabase.table("questionnaire_responses").delete().eq("user_id", user_id).execute()
            supabase.table("profiles").delete().eq("id", user_id).execute()
            print(f"Cleaned up data for user {user_id}")
        except Exception as e:
            print(f"Error during teardown for factory user {user_id}: {e}")
