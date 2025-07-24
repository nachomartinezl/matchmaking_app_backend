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

# The most important fixture: A factory to create and clean up test users
@pytest.fixture(scope="function")
def test_user_factory():
    created_users = []

    def _create_user():
        test_email = f"test-user-{uuid4()}@example.com"
        test_password = "password123"

        response = supabase.auth.sign_up({
            "email": test_email,
            "password": test_password,
        })
        
        if response.user is None:
            raise Exception("Failed to create test user in Supabase Auth.")

        new_user = response.user
        created_users.append(new_user.id)
        
        print(f"\nCREATED Test User: {new_user.id} ({new_user.email})")
        return {"id": new_user.id, "email": new_user.email}

    yield _create_user

    supabase.auth.admin

    # --- Teardown ---
    print(f"\nTEARDOWN: Deleting {len(created_users)} test users...")
    for user_id in created_users:
        try:
            supabase.auth.admin.delete_user(user_id)
            print(f"DELETED Test User: {user_id}")
        except Exception as e:
            print(f"ERROR deleting user {user_id}: {e}")