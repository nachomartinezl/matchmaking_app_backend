import json
import numpy as np
from uuid import UUID
from ..database import supabase
from fastapi.encoders import jsonable_encoder
from datetime import date, datetime

# --- Configuration ---
VECTOR_SIZE = 128
try:
    with open("feature_map.json", "r") as f:
        FEATURE_MAP = json.load(f)
except FileNotFoundError:
    print("FATAL ERROR: feature_map.json not found. Cannot generate embeddings.")
    FEATURE_MAP = {}

NORMALIZATION_RANGES = {
    "height_cm": (140, 210),
    "hexaco": (1, 5),
    "attachment": (5, 35),
    "values": (0, 8),
}


# --- Helper Function for Normalization ---
def normalize(value, min_val, max_val):
    """Normalize a value to a 0-1 scale."""
    if value is None or max_val - min_val == 0:
        return 0.0
    # Clamp the value to be within the expected range before normalizing
    clamped_value = max(min_val, min(value, max_val))
    return (clamped_value - min_val) / (max_val - min_val)


def serialize_dates(data: dict) -> dict:
    """Convert datetime/date objects in dict to ISO 8601 strings."""
    for k, v in data.items():
        if isinstance(v, datetime):
            data[k] = v.isoformat()
    return data


# --- Main Service Functions ---


async def get_full_profile(user_id: UUID) -> dict | None:
    """Fetches the complete profile row, including test_scores, as a dictionary."""
    response = (
        supabase.table("profiles").select("*").eq("id", str(user_id)).single().execute()
    )
    return response.data if response.data else None


async def simple_upsert_profile(profile_update_data: dict):
    """
    Upserts profile data without touching embeddings.
    For lead capture incremental steps.
    """
    if not profile_update_data:
        return None

    payload = jsonable_encoder(
        profile_update_data,
        custom_encoder={
            date: lambda d: d.isoformat(),
            datetime: lambda dt: dt.isoformat(),
        },
    )
    response = supabase.table("profiles").upsert(payload).execute()
    if not response.data:
        print("Failed to upsert profile:", profile_update_data.get("id"))
        return None
    return response.data[0]


async def _rebuild_and_save_embedding(profile_id: UUID) -> bool:
    """
    Private helper to rebuild and save a user's embedding.
    Returns True on success, False on failure.
    """
    full_profile = await get_full_profile(profile_id)
    if not full_profile:
        print(f"Could not fetch profile for user {profile_id} to rebuild embedding.")
        return False

    embedding_vector = await generate_master_embedding(full_profile)
    response = (
        supabase.table("profiles")
        .update({"embedding": embedding_vector})
        .eq("id", str(profile_id))
        .execute()
    )
    if not response.data:
        print(f"CRITICAL: Failed to save rebuilt embedding for user {profile_id}")
        return False
    return True


async def upsert_profile_and_rebuild_embedding(
    user_id: UUID, profile_update_data: dict
):
    """
    Upserts profile data, then rebuilds the master embedding.
    """
    if not profile_update_data:
        return None

    profile_update_data["id"] = str(user_id)
    upsert_response = supabase.table("profiles").upsert(profile_update_data).execute()
    if not upsert_response.data:
        print(f"Failed to upsert profile for user {user_id}")
        return None

    if not await _rebuild_and_save_embedding(user_id):
        # Even if embedding fails, the profile data was saved.
        # The return indicates the overall success of the operation.
        # Depending on requirements, you might want to handle this differently.
        print(f"Profile data saved, but embedding rebuild failed for {user_id}.")

    return {"success": True, "data": await get_full_profile(user_id)}


async def update_test_scores_and_rebuild_embedding(user_id: UUID, new_scores: dict):
    """
    Merges new test scores, saves them, and rebuilds the embedding.
    """
    full_profile = await get_full_profile(user_id)
    if not full_profile:
        return {"success": False, "message": f"Profile {user_id} not found."}

    existing_scores = full_profile.get("test_scores") or {}
    existing_scores.update(new_scores)

    scores_response = (
        supabase.table("profiles")
        .update({"test_scores": existing_scores})
        .eq("id", str(user_id))
        .execute()
    )
    if not scores_response.data:
        return {"success": False, "message": "Failed to save updated test scores."}

    if not await _rebuild_and_save_embedding(user_id):
        return {
            "success": False,
            "message": "Scores saved, but embedding rebuild failed.",
        }

    print(f"Test scores and embedding for {user_id} have been rebuilt and saved.")
    return {"success": True, "data": await get_full_profile(user_id)}


def _process_profile_attributes(embedding: np.ndarray, profile_data: dict):
    """Processes profile attributes and updates the embedding vector."""
    for key, value in profile_data.items():
        if value is None:
            continue

        # Categorical data
        feature_key = f"profile_{key}_{str(value).lower().replace(' ', '_')}"
        if feature_key in FEATURE_MAP:
            embedding[FEATURE_MAP[feature_key]] = 1.0

        # Numerical data
        feature_key_numeric = f"profile_{key}"
        if feature_key_numeric in FEATURE_MAP:
            if key in NORMALIZATION_RANGES:
                min_val, max_val = NORMALIZATION_RANGES[key]
                embedding[FEATURE_MAP[feature_key_numeric]] = normalize(
                    value, min_val, max_val
                )


def _process_test_scores(embedding: np.ndarray, test_scores: dict):
    """Processes test scores and updates the embedding vector."""
    if not test_scores:
        return

    # HEXACO
    if "Factor Scores" in test_scores:
        min_val, max_val = NORMALIZATION_RANGES["hexaco"]
        for factor, score in test_scores["Factor Scores"].items():
            feature_key = f"test_hexaco_{factor.lower().replace(' ', '-')}"
            if feature_key in FEATURE_MAP:
                embedding[FEATURE_MAP[feature_key]] = normalize(score, min_val, max_val)

    # Attachment Styles
    if "Attachment Style Scores" in test_scores:
        min_val, max_val = NORMALIZATION_RANGES["attachment"]
        for style, score in test_scores["Attachment Style Scores"].items():
            feature_key = f"test_attachment_{style.lower().replace(' ', '-')}"
            if feature_key in FEATURE_MAP:
                embedding[FEATURE_MAP[feature_key]] = normalize(score, min_val, max_val)

    # Values
    if "Values Scores" in test_scores:
        min_val, max_val = NORMALIZATION_RANGES["values"]
        for value_name, score in test_scores["Values Scores"].items():
            feature_key = f"test_values_{value_name.lower()}"
            if feature_key in FEATURE_MAP:
                embedding[FEATURE_MAP[feature_key]] = normalize(score, min_val, max_val)

    # MBTI
    if "MBTI Type" in test_scores:
        feature_key = f"test_mbti_type_{test_scores['MBTI Type'].lower()}"
        if feature_key in FEATURE_MAP:
            embedding[FEATURE_MAP[feature_key]] = 1.0


async def generate_master_embedding(profile_data: dict) -> list[float]:
    """
    Generates the master embedding vector from a user's full profile data
    using the feature_map.json.
    """
    embedding = np.zeros(VECTOR_SIZE, dtype=np.float32)
    _process_profile_attributes(embedding, profile_data)
    _process_test_scores(embedding, profile_data.get("test_scores"))
    return embedding.tolist()


async def get_profile_by_email(email: str) -> dict | None:
    response = (
        supabase.table("profiles").select("*").ilike("email", email).limit(1).execute()
    )
    return response.data[0] if response.data else None
