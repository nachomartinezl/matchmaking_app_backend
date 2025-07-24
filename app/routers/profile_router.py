from fastapi import APIRouter, HTTPException, Body
from uuid import UUID
from ..models import ProfileUpdate, ProfileOut
from ..services import profile_service

router = APIRouter(prefix="/profiles", tags=["Profiles"])

@router.get("/{user_id}", response_model=ProfileOut)
async def get_user_profile(user_id: UUID):
    """
    Retrieve a user's complete profile by their unique user ID.
    """
    # FIX: Call the correct function name: get_full_profile
    profile = await profile_service.get_full_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    # We return the dictionary directly, Pydantic handles the conversion
    return profile

@router.put("/{user_id}", response_model=ProfileOut)
async def upsert_user_profile(user_id: UUID, profile_data: ProfileUpdate):
    """
    Create or update a user's profile from the signup form or profile edit page.
    This triggers a full rebuild of the user's embedding vector.
    """
    # Let's call the upsert function directly and ensure the data is passed as a dict
    updated_profile = await profile_service.upsert_profile_and_rebuild_embedding(
        user_id, profile_data.dict(exclude_unset=True)
    )
    if not updated_profile:
        raise HTTPException(status_code=500, detail="Failed to create or update profile.")
    return updated_profile