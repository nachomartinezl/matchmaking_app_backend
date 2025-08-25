from fastapi import APIRouter, HTTPException
from uuid import UUID, uuid4
from datetime import datetime, timezone
from ..models import ProfileUpdate, ProfileOut
from ..services import profile_service
from ..services.email_service import send_verification_email, send_welcome_email

router = APIRouter(prefix="/profiles", tags=["Profiles"])

# ========== Start signup (lead capture) ==========
# In your profiles router file (e.g., routers/profiles.py)

@router.post("", response_model=dict)
async def start_profile(profile_data: ProfileUpdate):
    """
    Creates a new profile or intelligently handles an existing one.
    - If email does not exist: Creates a new profile and sends verification.
    - If email exists on an INCOMPLETE & UNVERIFIED profile: Updates info, re-sends verification.
    - If email exists on an INCOMPLETE & VERIFIED profile: Returns existing ID to fast-track user.
    - If email exists on a COMPLETE profile: Raises a 409 Conflict error.
    """
    minimal_required = ["first_name", "last_name", "dob", "email"]
    data = profile_data.model_dump(exclude_unset=True)

    missing = [f for f in minimal_required if not data.get(f)]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required fields: {', '.join(missing)}")

    existing = await profile_service.get_profile_by_email(data["email"])
    
    if existing:
        # Case 1: Profile is complete and active. Block this.
        if existing.get("is_complete"):
            raise HTTPException(
                status_code=409,
                detail="A profile with this email already exists."
            )
        
        profile_id = existing["id"]
        
        # Case 2: Profile is incomplete but already verified. Fast-track them.
        if existing.get("email_verified"):
            # Don't send an email. Just return the ID so the frontend can proceed.
            return {"id": str(profile_id), "status": "verified_resume"}

        # Case 3: Profile is incomplete and NOT verified. Treat as a resume/retry.
        update_payload = {
            "id": str(profile_id),
            "first_name": data["first_name"],
            "last_name": data["last_name"],
            "dob": data["dob"]
        }
        await profile_service.simple_upsert_profile(update_payload)
        
        # Re-send verification email.
        await send_verification_email(email=data["email"], profile_id=profile_id)
        
        return {"id": str(profile_id), "status": "unverified_resume"}

    # Case 4: Email is brand new. Create a new profile.
    profile_id = uuid4()
    data["id"] = str(profile_id)
    data["is_complete"] = False
    data["email_verified"] = False
    # I removed `progress=1` as it seems less relevant in a single-submit model

    result = await profile_service.simple_upsert_profile(data)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create profile")

    await send_verification_email(email=data["email"], profile_id=profile_id)

    return {"id": str(profile_id), "status": "new_profile"}


# ========== Incremental step update ==========
@router.patch("/{profile_id}", response_model=ProfileOut)
async def update_profile_step(profile_id: UUID, profile_data: ProfileUpdate):
    """
    Partial update for a profile step.
    """
    update_data = profile_data.model_dump(exclude_unset=True, mode="json")
    update_data["id"] = str(profile_id)

    result = await profile_service.simple_upsert_profile(update_data)
    if not result:
        raise HTTPException(500, "Failed to update profile step")

    return ProfileOut(**result)

# ========== Mark profile complete ==========
@router.post("/{profile_id}/complete", response_model=ProfileOut)
async def complete_profile(profile_id: UUID):
    """
    Mark profile as complete, send welcome email if verified.
    """
    profile = await profile_service.get_full_profile(profile_id)
    if not profile:
        raise HTTPException(404, "Profile not found")

    update_data = {
        "id": str(profile_id),
        "is_complete": True,
        "completed_at": datetime.now(timezone.utc)
    }

    if not profile.get("welcome_sent") and profile.get("email_verified"):
        await send_welcome_email(profile["email"], profile.get("first_name", ""))
        update_data["welcome_sent"] = True

    await profile_service.simple_upsert_profile(update_data)

    updated = await profile_service.get_full_profile(profile_id)
    return ProfileOut(**updated)

# ========== Fetch profile ==========
@router.get("/{profile_id}", response_model=ProfileOut)
async def get_user_profile(profile_id: UUID):
    profile = await profile_service.get_full_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return ProfileOut(**profile)
