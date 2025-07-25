from uuid import UUID
from ..database import supabase
from ..models import QuestionnaireSubmit
from .profile_service import update_test_scores_and_rebuild_embedding
from .scoring_service import calculate_scores_from_submission

async def list_questionnaires():
    """Fetches a list of all available questionnaires."""
    resp = supabase.table('questionnaires').select('id, namespace, name').execute()
    # A more detailed implementation might fetch questions for each, but this is fine.
    return resp.data if resp.data else []

async def get_questionnaire(q_id: str):
    """Fetches the full details of a single questionnaire, including its questions and options."""
    q_resp = supabase.table('questionnaires').select('*').eq('id', q_id).single().execute()
    if not q_resp.data:
        return None
    q = q_resp.data

    qs_resp = supabase.table('questions').select('id, question_text, position').eq('questionnaire_id', q_id).order('position').execute()
    qs = qs_resp.data

    for question in qs:
        opts_resp = supabase.table('options').select('id, option_text, position').eq('question_id', question['id']).order('position').execute()
        question['options'] = opts_resp.data

    q['questions'] = qs
    return q

async def submit_questionnaire_responses(submission: QuestionnaireSubmit):
    """
    Saves raw responses, calculates scores, and triggers a full profile/embedding rebuild.
    This is the primary entry point after a user completes a test.
    """
    # 1. Save raw answers for auditing purposes
    raw_response_insert = {
        "user_id": str(submission.user_id),
        "questionnaire": submission.questionnaire,
        "responses": submission.responses
    }
    supabase.table("questionnaire_responses").insert(raw_response_insert).execute()
    print(f"Raw responses saved for user {submission.user_id} for questionnaire '{submission.questionnaire}'.")

    # 2. Calculate the structured scores using the dedicated scoring service
    try:
        calculated_scores = calculate_scores_from_submission(submission)
        if not calculated_scores:
            return {"success": False, "message": f"No scoring logic implemented for '{submission.questionnaire}'."}
    except Exception as e:
        return {"success": False, "message": f"An error occurred during scoring: {e}"}
    
    print(f"Calculated scores for '{submission.questionnaire}': {calculated_scores}")
    
    # 3. Hand off to the profile service to save scores and rebuild the master embedding
    result = await update_test_scores_and_rebuild_embedding(submission.user_id, calculated_scores)
    
    if result and result.get("success"):
        return {"success": True, "message": "Successfully processed questionnaire and rebuilt user profile embedding."}
    else:
        # Pass the error message from the profile service up
        error_message = result.get("message", "An unknown error occurred in the profile service.")
        return {"success": False, "message": error_message}