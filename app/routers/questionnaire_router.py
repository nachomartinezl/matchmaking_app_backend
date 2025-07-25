from fastapi import APIRouter, HTTPException
from typing import List
from uuid import UUID
from ..models import QuestionnaireOut, QuestionnaireSubmit
from ..services import questionnaire_service

router = APIRouter(
    prefix="/questionnaires",
    tags=["Questionnaires"]
)

@router.get("/", response_model=List[QuestionnaireOut])
async def fetch_all_questionnaires():
    """
    Retrieves a list of all available questionnaires in the system.
    Note: Depending on the implementation of list_questionnaires, this might be a heavy operation.
    """
    questionnaires = await questionnaire_service.list_questionnaires()
    # A robust implementation would handle the full model transformation here if needed.
    # For now, we assume the service returns data that can be parsed into QuestionnaireOut.
    return questionnaires

@router.get("/{q_id}", response_model=QuestionnaireOut)
async def fetch_questionnaire(q_id: UUID):
    """
    Fetches the full details of a single questionnaire by its ID,
    including all its questions and their respective options.
    """
    q = await questionnaire_service.get_questionnaire(str(q_id))
    if not q:
        raise HTTPException(status_code=404, detail="Questionnaire not found")
    return q

@router.post("/submit", status_code=201)
async def submit_answers(submission: QuestionnaireSubmit):
    """
    Endpoint for a user to submit their answers to a questionnaire.
    This saves the raw answers and triggers a rebuild of the user's master embedding vector.
    """
    result = await questionnaire_service.submit_questionnaire_responses(submission)
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("message", "An unknown error occurred."))
        
    return result