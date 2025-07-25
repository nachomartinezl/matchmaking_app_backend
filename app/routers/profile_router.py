from fastapi import APIRouter, HTTPException, Body
from uuid import UUID
from ..models import ProfileUpdate, ProfileOut
from ..services import profile_service

router = APIRouter(prefix="/profiles", tags=["Profiles"])

from datetime import datetime

@router.get("/{user_id}", response_model=ProfileOut)
async def get_user_profile(user_id: UUID):
    """
    Retrieve a user's complete profile by their unique user ID.
    """
    profile = await profile_service.get_full_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Manually convert string dates to datetime objects
    if isinstance(profile.get('created_at'), str):
        profile['created_at'] = datetime.fromisoformat(profile['created_at'])
    if isinstance(profile.get('updated_at'), str):
        profile['updated_at'] = datetime.fromisoformat(profile['updated_at'])

    return profile

@router.put("/{user_id}", response_model=ProfileOut)
async def upsert_user_profile(user_id: UUID, profile_data: ProfileUpdate):
    """
    Create or update a user's profile from the signup form or profile edit page.
    This triggers a full rebuild of the user's embedding vector.
    """
    update_data = profile_data.model_dump(mode='json', exclude_unset=True)

    result = await profile_service.upsert_profile_and_rebuild_embedding(
        user_id, update_data
    )
    if not result or not result.get("success"):
        raise HTTPException(status_code=500, detail="Failed to create or update profile.")

    updated_profile = result["data"]

    # Manually convert string dates to datetime objects
    if isinstance(updated_profile.get('created_at'), str):
        updated_profile['created_at'] = datetime.fromisoformat(updated_profile['created_at'])
    if isinstance(updated_profile.get('updated_at'), str):
        updated_profile['updated_at'] = datetime.fromisoformat(updated_profile['updated_at'])

    return ProfileOut(**updated_profile)