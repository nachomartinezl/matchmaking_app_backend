import pytest
from uuid import uuid4

# All tests in this file use the `client` and `managed_user` fixtures.
# The `managed_user` fixture creates a user and a basic profile, and cleans up after the test.
pytestmark = pytest.mark.usefixtures("client", "managed_user")


def test_update_profile_full_data(client, managed_user):
    """
    Tests updating a user's profile with a comprehensive set of valid data.
    """
    user_id = managed_user["id"]

    payload = {
        "first_name": "Updated",
        "last_name": "Name",
        "goal": "relationship",
        "smoking": "never",
        "dob": "1990-01-01",
        "gender": "female",
        "country": "US",
        "preference": "men",
        "height_feet": 5,
        "height_inches": 7,
        "religion": "atheism",
        "pets": "none",
        "drinking": "sometimes",
        "kids": "not_sure",
        "description": "An updated test user.",
        "profile_picture_url": "https://example.com/updated_profile.jpg",
        "gallery_urls": [
            "https://example.com/1.jpg",
            "https://example.com/2.jpg",
        ],
    }

    # Use PATCH to update the profile
    resp_patch = client.patch(f"/profiles/{user_id}", json=payload)
    assert resp_patch.status_code == 200

    # Verify the changes by fetching the profile
    resp_get = client.get(f"/profiles/{user_id}")
    assert resp_get.status_code == 200
    data = resp_get.json()

    assert data["first_name"] == "Updated"
    assert data["country"] == "US"
    assert data["height_cm"] == 170  # Derived from 5'7"
    assert data["height_feet"] == 5
    assert data["height_inches"] == 7
    assert len(data["gallery_urls"]) == 2


def test_get_profile(client, managed_user):
    """
    Tests fetching a user's profile.
    """
    user_id = managed_user["id"]

    resp = client.get(f"/profiles/{user_id}")
    assert resp.status_code == 200
    data = resp.json()

    assert data["id"] == user_id
    assert data["first_name"] == "Managed" # From the fixture
    assert data["email"] == managed_user["email"]


def test_update_profile_invalid_gallery_urls(client, managed_user):
    """
    Tests that the API correctly handles an attempt to add more than the allowed
    number of gallery URLs.
    """
    user_id = managed_user["id"]

    # Create a list of 7 URLs, which is one more than the allowed limit of 6
    invalid_gallery_urls = [f"https://example.com/{i}.jpg" for i in range(7)]

    payload = {
        "gallery_urls": invalid_gallery_urls
    }

    resp = client.patch(f"/profiles/{user_id}", json=payload)

    # The request should be rejected as a validation error
    assert resp.status_code == 422 # Unprocessable Entity
    error_detail = resp.json()["detail"][0]
    assert "ensure this value has at most 6 items" in error_detail["msg"]
