from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class ActivityLevel(str, Enum):
    sedentary = "sedentary"
    lightly_active = "lightly_active"
    moderately_active = "moderately_active"
    very_active = "very_active"


class PrimaryGoal(str, Enum):
    weight_loss = "weight_loss"
    muscle_gain = "muscle_gain"
    maintenance = "maintenance"
    manage_condition = "manage_condition"
    healthy_eating = "healthy_eating"


# Supported conditions — used for condition-aware filtering in Phase 4
SUPPORTED_CONDITIONS = [
    "diabetes_type2",
    "hypertension",
    "chronic_kidney_disease",
    "pcos",
    "celiac",
    "lactose_intolerant",
    "heart_disease",
    "obesity",
]


# ── Request schemas ───────────────────────────────────


class HealthProfileUpdate(BaseModel):
    age: Optional[int] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    gender: Optional[str] = None
    conditions: Optional[list[str]] = None
    dietary_restrictions: Optional[list[str]] = None
    allergies: Optional[list[str]] = None
    preferred_cuisines: Optional[list[str]] = None
    daily_calorie_target: Optional[int] = None
    primary_goal: Optional[PrimaryGoal] = None
    activity_level: Optional[ActivityLevel] = None


# ── Response schemas ──────────────────────────────────


class HealthProfileResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    user_id: int
    age: Optional[int]
    weight_kg: Optional[float]
    height_cm: Optional[float]
    gender: Optional[str]
    conditions: list[str]
    dietary_restrictions: list[str]
    allergies: list[str]
    preferred_cuisines: list[str]
    daily_calorie_target: Optional[int]
    primary_goal: Optional[str]
    activity_level: Optional[str]
    updated_at: datetime
