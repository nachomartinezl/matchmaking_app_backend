from fastapi import APIRouter, HTTPException
from uuid import UUID
from ..services import match_service

router = APIRouter(prefix="/matches", tags=["Matching"])

@router.post("/run/{user_id}", status_code=200)
async def run_matchmaking(user_id: UUID):
    result = await match_service.find_matches_for_user(user_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return {"message": result["message"]}