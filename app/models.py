from pydantic import BaseModel, EmailStr, Field, model_validator, field_validator
from typing import List, Optional, Annotated
from uuid import UUID
from enum import Enum
from datetime import date, datetime

# ===== helpers =====

def _to_cm(feet: int, inches: int) -> int:
    return int(round((feet * 12 + inches) * 2.54))

def _to_feet_inches(cm: int) -> tuple[int, int]:
    total_inches = round(cm / 2.54)
    return total_inches // 12, total_inches % 12

CountryCode = Annotated[str, Field(min_length=2, max_length=2, pattern="^[A-Z]{2}$")]

# (Optional) strict ISO validation:
# import pycountry
# ISO_CODES = {c.alpha_2 for c in pycountry.countries}
# ...then in a validator: assert v in ISO_CODES

# ===================================================================
# ENUMs to match the PostgreSQL ENUM types for data integrity
# ===================================================================

class UserGender(str, Enum):
    male = "male"
    female = "female"
    non_binary = "non-binary"
    other = "other"

class InterestPreference(str, Enum):
    women = "women"
    men = "men"
    both = "both"
    not_sure = "not_sure"

class ReligionType(str, Enum):
    atheism = "atheism"
    buddhism = "buddhism"
    christianity = "christianity"
    hinduism = "hinduism"
    islam = "islam"
    judaism = "judaism"
    other = "other"
    none = "none"

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

class SmokingHabit(str, Enum):
    regularly = "regularly"
    when_drink = "when_drink"
    sometimes = "sometimes"
    never = "never"

class DrinkingHabit(str, Enum):
    often = "often"
    on_holidays = "on_holidays"
    sometimes = "sometimes"
    never = "never"

class KidsStatus(str, Enum):
    i_have = "i_have"
    i_want_to = "i_want_to"
    i_do_not_want = "i_do_not_want"
    not_sure = "not_sure"

class RelationshipGoal(str, Enum):
    friends = "friends"
    casual = "casual"
    relationship = "relationship"
    not_sure = "not_sure"

# ===================================================================
# Profile Models (for the public.profiles table)
# ===================================================================

class ProfileUpdate(BaseModel):
    # identity
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None

    # demographics
    dob: Optional[date] = None
    gender: Optional["UserGender"] = None
    country: Optional[CountryCode] = None

    preference: Optional["InterestPreference"] = None

    # height (canonical cm; accept feet/inches from UI)
    height_cm: Optional[int] = None
    height_feet: Optional[int] = Field(default=None, ge=0, le=9)
    height_inches: Optional[int] = Field(default=None, ge=0, le=11)

    # lifestyle
    religion: Optional["ReligionType"] = None
    pets: Optional["PetsPreference"] = None
    smoking: Optional["SmokingHabit"] = None
    drinking: Optional["DrinkingHabit"] = None
    kids: Optional["KidsStatus"] = None
    goal: Optional["RelationshipGoal"] = None

    description: Optional[str] = None

    # photos
    profile_picture_url: Optional[str] = None
    gallery_urls: Optional[List[str]] = None  # up to 6

    # --- validators ---
    @model_validator(mode="before")
    def set_height_cm_from_feet_inches(cls, values):
        hf, hi, hcm = values.get("height_feet"), values.get("height_inches"), values.get("height_cm")
        if hcm is None and hf is not None and hi is not None:
            values["height_cm"] = _to_cm(hf, hi)
        return values

    @field_validator("gallery_urls")
    @classmethod
    def gallery_max_six(cls, v):
        if v and len(v) > 6:
            raise ValueError("gallery_urls can have at most 6 items")
        return v

    @field_validator("country")
    @classmethod
    def country_upper(cls, v):
        return v.upper() if v else v
        # For strict ISO:
        # if v and v.upper() not in ISO_CODES: raise ValueError("Invalid ISO country code")
        # return v.upper() if v else v

class ProfileOut(BaseModel):
    id: UUID

    # identity
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[EmailStr]

    # demographics
    dob: Optional[date]
    gender: Optional["UserGender"]
    country: Optional[CountryCode]
    preference: Optional["InterestPreference"]

    # height
    height_cm: Optional[int]
    height_feet: Optional[int] = None
    height_inches: Optional[int] = None

    # lifestyle
    religion: Optional["ReligionType"]
    pets: Optional["PetsPreference"]
    smoking: Optional["SmokingHabit"]
    drinking: Optional["DrinkingHabit"]
    kids: Optional["KidsStatus"]
    goal: Optional["RelationshipGoal"]

    description: Optional[str]

    # photos
    profile_picture_url: Optional[str]
    gallery_urls: Optional[List[str]] = None

    # signup / state flags  ✅ add these
    email_verified: Optional[bool] = None
    is_complete: Optional[bool] = None
    progress: Optional[int] = None
    welcome_sent: Optional[bool] = None
    completed_at: Optional[datetime] = None

    # ML/meta
    embedding: Optional[List[float]] = None
    test_scores: Optional[dict] = None

    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def derive_imperial(self):
        if self.height_cm is not None and (self.height_feet is None or self.height_inches is None):
            f, i = _to_feet_inches(self.height_cm)
            object.__setattr__(self, "height_feet", f)
            object.__setattr__(self, "height_inches", i)
        return self

    class Config:
        from_attributes = True

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
        from_attributes = True

class QuestionOut(BaseModel):
    id: UUID
    question_text: str
    position: int
    options: List[OptionOut]

    class Config:
        from_attributes = True

class QuestionnaireOut(BaseModel):
    id: UUID
    namespace: str
    name: str
    questions: List[QuestionOut]

    class Config:
        from_attributes = True