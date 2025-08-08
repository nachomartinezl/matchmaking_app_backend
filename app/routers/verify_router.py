# app/routes/verify.py
from fastapi import APIRouter, HTTPException
from uuid import UUID
import jwt
import os
from ..services import profile_service

router = APIRouter(tags=["Email Verification"])

# Secret key for signing verification tokens
EMAIL_VERIFY_SECRET = os.getenv("EMAIL_VERIFY_SECRET", "change-me")

@router.get("/verify")
async def verify_email(token: str):
    """
    Called when the user clicks the email verification link.
    Decodes the token and marks the profile as email_verified = true.
    """
    try:
        payload = jwt.decode(token, EMAIL_VERIFY_SECRET, algorithms=["HS256"])
        profile_id = payload.get("profile_id")
        if not profile_id:
            raise HTTPException(status_code=400, detail="Invalid token: missing profile_id")
        # Ensure it's a valid UUID format
        try:
            profile_uuid = UUID(profile_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid profile_id format")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Verification link has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail="Invalid verification token")

    # Update profile to mark email as verified
    updated = await profile_service.simple_upsert_profile({
        "id": str(profile_uuid),
        "email_verified": True
    })
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update email verification status")

    # Optional: here you could serve an HTML success page instead of JSON
    return {
        "message": "Email verified successfully",
        "profile_id": str(profile_uuid)
    }
