from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from uuid import UUID
from datetime import date
from enum import Enum
from datetime import date, datetime

# ===================================================================
# ENUMs to match the PostgreSQL ENUM types for data integrity
# ===================================================================

class UserGender(str, Enum):
    male = "male"
    female = "female"
    non_binary = "non-binary"
    other = "other"
    prefer_not_to_say = "prefer-not-to-say"

class InterestPreference(str, Enum):
    women = "women"
    men = "men"
    both = "both"

class ReligionType(str, Enum):
    atheism = "atheism"
    buddhism = "buddhism"
    christianity = "christianity"
    hinduism = "hinduism"
    islam = "islam"
    judaism = "judaism"
    other = "other"
    skip = "skip"

class PetsPreference(str, Enum):
    birds = "birds"
    cats = "cats"
    dogs = "dogs"
    fish = "fish"
    hamsters = "hamsters"
    rabbits = "rabbits"
    snakes = "snakes"
    turtles = "turtles"
    none = "none"
    skip = "skip"

class SmokingHabit(str, Enum):
    regularly = "regularly"
    when_drink = "when_drink"
    sometimes = "sometimes"
    never = "never"
    skip = "skip"

class DrinkingHabit(str, Enum):
    often = "often"
    on_holidays = "on_holidays"
    sometimes = "sometimes"
    never = "never"
    skip = "skip"

class KidsStatus(str, Enum):
    not_yet = "not_yet"
    childfree = "childfree"
    one = "1"
    two = "2"
    three = "3"
    more_than_3 = "more_than_3"
    skip = "skip"

class MaritalStatusType(str, Enum):
    single = "single"
    married = "married"
    in_relationship = "in_relationship"
    divorced = "divorced"
    separated = "separated"
    skip = "skip"

class RelationshipGoal(str, Enum):
    friends = "friends"
    casual = "casual"
    relationship = "relationship"

# ===================================================================
# Profile Models (for the public.profiles table)
# ===================================================================

class ProfileUpdate(BaseModel):
    """
    Model for creating or updating a profile. All fields are optional
    to allow for partial updates as the user moves through signup steps.
    """
    first_name: Optional[str]
    last_name: Optional[str]
    dob: Optional[date]
    gender: Optional[UserGender]
    country: Optional[str]
    preference: Optional[InterestPreference]
    height_cm: Optional[int]
    religion: Optional[ReligionType]
    pets: Optional[PetsPreference]
    smoking: Optional[SmokingHabit]
    drinking: Optional[DrinkingHabit]
    kids: Optional[KidsStatus]
    marital_status: Optional[MaritalStatusType]
    goal: Optional[RelationshipGoal]
    description: Optional[str]
    profile_picture_url: Optional[str]

class ProfileOut(BaseModel):
    """
    Model for returning a full profile to the client. This represents a
    row from the public.profiles table.
    """
    id: UUID
    first_name: Optional[str]
    last_name: Optional[str]
    dob: Optional[date]
    gender: Optional[UserGender]
    country: Optional[str]
    preference: Optional[InterestPreference]
    height_cm: Optional[int]
    religion: Optional[ReligionType]
    pets: Optional[PetsPreference]
    smoking: Optional[SmokingHabit]
    drinking: Optional[DrinkingHabit]
    kids: Optional[KidsStatus]
    marital_status: Optional[MaritalStatusType]
    goal: Optional[RelationshipGoal]
    description: Optional[str]
    profile_picture_url: Optional[str]
    embedding: Optional[List[float]] = None
    created_at: datetime  # Changed from date to datetime
    updated_at: datetime  # Changed from date to datetime

    class Config:
        from_attributes = True # Allows Pydantic to read data from ORM models (or dicts)

# ===================================================================
# Original Models for other application features
# ===================================================================

class QuestionnaireSubmit(BaseModel):
    user_id: UUID
    questionnaire: str
    responses: List[int]

class MatchResult(BaseModel):
    user_id: UUID
    match_id: UUID
    score: float

# Metadata models for dynamic questionnaires
class OptionOut(BaseModel):
    id: UUID
    option_text: str
    position: int

    class Config:
        orm_mode = True

class QuestionOut(BaseModel):
    id: UUID
    question_text: str
    position: int
    options: List[OptionOut]

    class Config:
        orm_mode = True

class QuestionnaireOut(BaseModel):
    id: UUID
    namespace: str
    name: str
    questions: List[QuestionOut]

    class Config:
        orm_mode = True