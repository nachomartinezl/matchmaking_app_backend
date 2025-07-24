from uuid import UUID
from ..database import supabase
from .profile_service import get_full_profile

async def find_matches_for_user(user_id: UUID, count: int = 20):
    """
    Finds and stores matches for a user using a multi-layered approach.
    """
    # 1. Get the current user's profile and preferences
    user_profile = await get_full_profile(user_id)
    if not user_profile or not user_profile.get('preference'):
        return {"success": False, "message": "User profile or preference not set."}

    user_preference = user_profile['preference']
    user_gender = user_profile['gender']
    user_embedding = user_profile.get('embedding')

    if not user_embedding:
        return {"success": False, "message": "User embedding not generated. Please complete questionnaires."}
        
    # 2. Layer 1: Hard Filter for sexual preference
    query = supabase.table("profiles").select("id")
    
    # Find people whose gender matches the user's preference
    if user_preference == 'men':
        query = query.eq('gender', 'male')
    elif user_preference == 'women':
        query = query.eq('gender', 'female')
    # If 'both', no gender filter is applied.

    # Find people whose preference includes the user's gender
    query = query.or_(f'preference.eq.{user_gender},preference.eq.both')
    
    # Exclude self
    query = query.neq('id', str(user_id))
    
    eligible_candidates_response = query.execute()
    
    if not eligible_candidates_response.data:
        return {"success": True, "message": "No eligible candidates found after filtering."}
        
    candidate_ids = [c['id'] for c in eligible_candidates_response.data]

    # 3. Layer 2: Soft Matching with pgvector
    matches_response = supabase.rpc('match_knn_filtered', {
        'user_embedding': user_embedding,
        'match_count': count,
        'candidate_ids': candidate_ids
    }).execute()

    if not matches_response.data:
        return {"success": True, "message": "No matches found in vector search."}
        
    # 4. Save the matches to the 'matches' table
    matches_to_insert = [
        {"user_id": str(user_id), "match_id": match['match_id'], "score": match['score']}
        for match in matches_response.data
    ]
    
    # Use upsert to avoid duplicate pending matches
    supabase.table("matches").upsert(matches_to_insert, on_conflict='user_id,match_id').execute()

    return {"success": True, "message": f"Successfully found and stored {len(matches_to_insert)} potential matches."}