import os
from dotenv import load_dotenv
import jwt
from datetime import datetime, timedelta, timezone

# Load variables from .env into environment
load_dotenv()

EMAIL_VERIFY_SECRET = os.getenv("EMAIL_VERIFY_SECRET")
if not EMAIL_VERIFY_SECRET:
    raise ValueError("EMAIL_VERIFY_SECRET is not set in the environment")

profile_id = "123e4567-e89b-12d3-a456-426614174000"

token = jwt.encode(
    {"profile_id": profile_id, "exp": datetime.now(timezone.utc) + timedelta(days=1)},
    EMAIL_VERIFY_SECRET,
    algorithm="HS256"
)

print(token)
