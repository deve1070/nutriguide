from typing import List, Optional

from pydantic import BaseModel, Field

# ── Request ───────────────────────────────────────────


class MealPlanRequest(BaseModel):
    days: int = Field(7, ge=1, le=14, description="Number of days to plan")
    meals_per_day: int = Field(
        3, ge=2, le=5, description="Meals per day (2=lunch+dinner, 3=all meals)"
    )
    max_calories_per_day: Optional[int] = Field(
        None, gt=0, description="Override daily calorie target from profile"
    )
    cuisine_preferences: Optional[List[str]] = Field(
        None, description="Override cuisine preferences from profile"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "days": 7,
                    "meals_per_day": 3,
                    "max_calories_per_day": 1800,
                    "cuisine_preferences": ["Mediterranean", "Ethiopian"],
                }
            ]
        }
    }


# ── Response ──────────────────────────────────────────


class MealSlot(BaseModel):
    meal_type: str  # breakfast | lunch | dinner | snack
    food_name: str
    food_description: str
    cuisine_type: str
    calories: int
    ingredients: str
    health_benefits: str
    cooking_method: str
    condition_safe: bool  # True = passed clinical rule filters
    similarity_score: float


class DayPlan(BaseModel):
    day: int
    day_name: str  # Monday, Tuesday, ...
    meals: List[MealSlot]
    total_calories: int
    daily_notes: str  # AI-generated tip for the day


class MealPlanSummary(BaseModel):
    total_days: int
    avg_daily_calories: float
    cuisines_included: List[str]
    conditions_applied: List[str]
    generation_notes: str  # overall plan rationale from LLM


class MealPlanResponse(BaseModel):
    plan_id: str
    days: List[DayPlan]
    summary: MealPlanSummary
