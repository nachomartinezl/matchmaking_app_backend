import json
import numpy as np
from uuid import UUID
from ..database import supabase

# --- Configuration ---
VECTOR_SIZE = 128
try:
    with open('feature_map.json', 'r') as f:
        FEATURE_MAP = json.load(f)
except FileNotFoundError:
    print("FATAL ERROR: feature_map.json not found. Cannot generate embeddings.")
    FEATURE_MAP = {}

# --- Helper Function for Normalization ---
def normalize(value, min_val, max_val):
    """Normalize a value to a 0-1 scale."""
    if value is None or max_val - min_val == 0:
        return 0.0
    # Clamp the value to be within the expected range before normalizing
    clamped_value = max(min_val, min(value, max_val))
    return (clamped_value - min_val) / (max_val - min_val)

# --- Main Service Functions ---

async def get_full_profile(user_id: UUID) -> dict | None:
    """Fetches the complete profile row, including test_scores, as a dictionary."""
    response = supabase.table("profiles").select("*").eq("id", str(user_id)).single().execute()
    return response.data if response.data else None

async def upsert_profile_and_rebuild_embedding(user_id: UUID, profile_update_data: dict):
    """
    Upserts profile data, then fetches the full profile to rebuild the master embedding.
    This is the primary function to call after signup or profile edits.
    """
    if not profile_update_data:
        print("No update data provided.")
        return None

    profile_update_data['id'] = str(user_id)
    
    # 1. Use UPSERT, not UPDATE. This will create if not exists, or update if it does.
    upsert_response = supabase.table("profiles").upsert(profile_update_data).execute()
    if not upsert_response.data:
        print(f"Failed to upsert profile for user {user_id}")
        return None
    print(f"Profile for {user_id} upserted successfully.")

    # 2. Fetch the complete, updated profile
    full_profile = await get_full_profile(user_id)
    if not full_profile:
        print(f"Could not fetch updated profile for user {user_id}")
        return None

    # 3. Rebuild the master embedding vector from the full profile
    embedding_vector = await generate_master_embedding(full_profile)
    
    # 4. Save the new embedding
    embedding_response = supabase.table("profiles").update({"embedding": embedding_vector}).eq("id", str(user_id)).execute()
    if not embedding_response.data:
        print(f"CRITICAL: Failed to save rebuilt embedding for user {user_id}")

    print(f"Embedding for {user_id} has been rebuilt and saved.")

    # Return the complete, updated profile
    return {"success": True, "data": await get_full_profile(user_id)}

async def update_test_scores_and_rebuild_embedding(user_id: UUID, new_scores: dict):
    """
    Fetches existing scores, merges new scores, saves them, and rebuilds the embedding.
    This is the primary function to call after a questionnaire is submitted.
    """
    # 1. Fetch the complete, current profile to get existing scores
    full_profile = await get_full_profile(user_id)
    if not full_profile:
        return {"success": False, "message": f"Could not find profile for user {user_id}"}

    # 2. Merge new scores with existing scores
    existing_scores = full_profile.get('test_scores') or {}
    existing_scores.update(new_scores)
    
    # 3. Update the 'test_scores' field in the database
    scores_update_payload = {"test_scores": existing_scores}
    scores_response = supabase.table("profiles").update(scores_update_payload).eq("id", str(user_id)).execute()
    if not scores_response.data:
         return {"success": False, "message": "Failed to save updated test scores."}

    # 4. Rebuild the master embedding with the newly updated scores in the profile
    # We update the local 'full_profile' object to avoid another DB call
    full_profile['test_scores'] = existing_scores
    embedding_vector = await generate_master_embedding(full_profile)

    # 5. Save the new embedding
    embedding_response = supabase.table("profiles").update({"embedding": embedding_vector}).eq("id", str(user_id)).execute()
    if not embedding_response.data:
        return {"success": False, "message": "CRITICAL: Failed to save rebuilt embedding."}

    print(f"Test scores and embedding for {user_id} have been rebuilt and saved.")
    return {"success": True, "data": await get_full_profile(user_id)}


async def generate_master_embedding(profile_data: dict) -> list[float]:
    """
    Generates the master embedding vector from a user's full profile data
    using the feature_map.json.
    """
    embedding = np.zeros(VECTOR_SIZE, dtype=np.float32)
    
    # --- 1. Process Profile Attributes (Categorical & Numerical) ---
    for key, value in profile_data.items():
        if value is None:
            continue
        
        # For categorical data (e.g., gender, smoking), we use one-hot encoding
        feature_key = f"profile_{key}_{str(value).lower().replace(' ', '_')}"
        if feature_key in FEATURE_MAP:
            index = FEATURE_MAP[feature_key]
            embedding[index] = 1.0
            
        # For numerical data (e.g., height), we normalize and place the value
        feature_key_numeric = f"profile_{key}"
        if feature_key_numeric in FEATURE_MAP:
            index = FEATURE_MAP[feature_key_numeric]
            # Example normalization for height (adjust min/max as needed)
            if key == "height_cm":
                embedding[index] = normalize(value, 140, 210)

    # --- 2. Process Test Scores from the 'test_scores' JSONB field ---
    test_scores = profile_data.get('test_scores')
    if test_scores:
        # HEXACO
        if 'Factor Scores' in test_scores:
            for factor, score in test_scores['Factor Scores'].items():
                feature_key = f"test_hexaco_{factor.lower().replace(' ', '-')}"
                if feature_key in FEATURE_MAP:
                    index = FEATURE_MAP[feature_key]
                    embedding[index] = normalize(score, 1, 5) # Normalize from 1-5 scale
        
        # Attachment Styles
        if 'Attachment Style Scores' in test_scores:
            for style, score in test_scores['Attachment Style Scores'].items():
                feature_key = f"test_attachment_{style.lower().replace(' ', '-')}"
                if feature_key in FEATURE_MAP:
                    index = FEATURE_MAP[feature_key]
                    # Assuming attachment scores are on a 1-7 scale for 5 questions (max 35)
                    embedding[index] = normalize(score, 5, 35) 
        
        # Values
        if 'Values Scores' in test_scores:
             for value_name, score in test_scores['Values Scores'].items():
                feature_key = f"test_values_{value_name.lower()}"
                if feature_key in FEATURE_MAP:
                    index = FEATURE_MAP[feature_key]
                    # Assuming values scores are on a 0-8 scale
                    embedding[index] = normalize(score, 0, 8)
        
        # MBTI
        if 'MBTI Type' in test_scores:
            feature_key = f"test_mbti_type_{test_scores['MBTI Type'].lower()}"
            if feature_key in FEATURE_MAP:
                index = FEATURE_MAP[feature_key]
                embedding[index] = 1.0

    return embedding.tolist() 