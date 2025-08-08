import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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