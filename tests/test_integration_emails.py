import pytest
from unittest.mock import patch

# All tests in this file use the `client` fixture.
pytestmark = pytest.mark.usefixtures("client")


def test_verification_email_sent_on_profile_creation(client, test_user_factory):
    """
    Tests that a verification email is triggered when a new profile is created.
    This test uses the test_user_factory directly instead of managed_user
    because managed_user already creates a profile, and we need to control
    the point of creation to patch the email function.
    """
    user = test_user_factory()

    with patch("app.routers.profile_router.send_verification_email") as mock_send_email:
        profile_data = {
            "first_name": "Email",
            "last_name": "Test",
            "dob": "2000-02-02",
            "email": user["email"],
        }
        response = client.post("/profiles", json=profile_data)
        assert response.status_code == 200

        mock_send_email.assert_called_once()
        # Clean up the created profile
        profile_id = response.json()["id"]
        from app.database import supabase
        supabase.table("profiles").delete().eq("id", profile_id).execute()


def test_welcome_email_sent_on_profile_completion(client, managed_user):
    """
    Tests that a welcome email is sent when a user's profile is marked as complete.
    """
    user_id = managed_user["id"]
    user_email = managed_user["email"]

    # Precondition: The user's email must be verified to get a welcome email.
    # We'll update the profile directly in the DB for this test setup.
    from app.database import supabase
    supabase.table("profiles").update({"email_verified": True}).eq("id", user_id).execute()

    # Now, mock the welcome email function and call the completion endpoint
    with patch("app.routers.profile_router.send_welcome_email") as mock_send_welcome:
        response = client.post(f"/profiles/{user_id}/complete")
        assert response.status_code == 200

        # Assert that the welcome email was sent with the correct details
        mock_send_welcome.assert_called_once()

        # The first argument to send_welcome_email should be the email, the second the first name
        call_args, _ = mock_send_welcome.call_args
        assert call_args[0] == user_email

        # Fetch the profile to get the first name for assertion
        profile_resp = client.get(f"/profiles/{user_id}")
        first_name = profile_resp.json()["first_name"]
        assert call_args[1] == first_name
