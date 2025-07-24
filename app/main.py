from fastapi import FastAPI
from .routers import profile_router, questionnaire_router, match_router

# Create the main FastAPI application instance
app = FastAPI(
    title="Matchmaking MVP Backend",
    description="API service for user profiles, dynamic questionnaires, and personality-based matchmaking.",
    version="1.0.0"
)

# --- Include all the application routers ---

# Handles creating/updating user profiles and rebuilding embeddings.
app.include_router(profile_router.router)

# Handles fetching questionnaires and submitting user answers.
app.include_router(questionnaire_router.router)

# Handles running the matchmaking algorithm and managing match status.
app.include_router(match_router.router)


# --- Root Endpoint ---

@app.get("/", tags=["Root"])
async def read_root():
    """
    A simple root endpoint to confirm the API is running.
    """
    return {"message": "Welcome to the Matchmaking MVP API!"}