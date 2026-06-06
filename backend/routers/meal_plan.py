from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.core.vector_store import VectorStore, get_vector_store
from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.health_profile import HealthProfile
from backend.models.meal_plan import MealPlan
from backend.models.user import User
from backend.schemas.meal_plan import (
    DayPlan,
    MealPlanRequest,
    MealPlanResponse,
    MealPlanSummary,
    MealSlot,
)
from backend.services.condition_filter import ConditionFilter, get_condition_filter
from backend.services.llm_client import LLMClient, get_llm_client
from backend.services.meal_planner import MealPlanner

router = APIRouter(prefix="/meal-plan", tags=["Meal Planner"])


def get_meal_planner(
    vector_store: VectorStore = Depends(get_vector_store),
    llm_client: LLMClient = Depends(get_llm_client),
    condition_filter: ConditionFilter = Depends(get_condition_filter),
) -> MealPlanner:
    return MealPlanner(
        vector_store=vector_store,
        llm_client=llm_client,
        condition_filter=condition_filter,
    )


@router.post(
    "/generate",
    response_model=MealPlanResponse,
    summary="Generate a personalized multi-day meal plan",
    description=(
        "Generates a complete meal plan based on your health profile. "
        "Applies condition-aware filtering, calorie targets, and cuisine preferences. "
        "No meal is repeated within the plan. Saves to database, replacing any existing plan."
    ),
)
def generate_meal_plan(
    payload: MealPlanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    planner: MealPlanner = Depends(get_meal_planner),
):
    # Load user health profile
    profile = (
        db.query(HealthProfile).filter(HealthProfile.user_id == current_user.id).first()
    )

    conditions = profile.conditions if profile else []
    dietary_restrictions = profile.dietary_restrictions if profile else []
    allergies = profile.allergies if profile else []
    cuisine_prefs = payload.cuisine_preferences or (
        profile.preferred_cuisines if profile else []
    )
    calorie_target = payload.max_calories_per_day or (
        profile.daily_calorie_target if profile else None
    )

    # Generate the plan
    raw = planner.generate(
        days=payload.days,
        meals_per_day=payload.meals_per_day,
        conditions=conditions,
        dietary_restrictions=dietary_restrictions,
        allergies=allergies,
        max_calories_per_day=calorie_target,
        cuisine_preferences=cuisine_prefs,
    )

    # Save to database (replaces any existing plan)
    planner.save_plan(
        plan_data=raw,
        user_id=current_user.id,
        db=db,
        days=payload.days,
    )

    # Map raw dicts → Pydantic response models
    day_plans = []
    for d in raw["days"]:
        meals = [
            MealSlot(
                meal_type=m.get("meal_type", "meal"),
                food_name=m.get("food_name", ""),
                food_description=m.get("food_description", ""),
                cuisine_type=m.get("cuisine_type", ""),
                calories=m.get("food_calories_per_serving", 0),
                ingredients=m.get("food_ingredients", ""),
                health_benefits=m.get("food_health_benefits", ""),
                cooking_method=m.get("cooking_method", ""),
                condition_safe=m.get("condition_safe", True),
                similarity_score=m.get("similarity_score", 0.0),
            )
            for m in d["meals"]
        ]
        day_plans.append(
            DayPlan(
                day=d["day"],
                day_name=d["day_name"],
                meals=meals,
                total_calories=d["total_calories"],
                daily_notes=d["daily_notes"],
            )
        )

    s = raw["summary"]
    summary = MealPlanSummary(
        total_days=s["total_days"],
        avg_daily_calories=s["avg_daily_calories"],
        cuisines_included=s["cuisines_included"],
        conditions_applied=s["conditions_applied"],
        generation_notes=s["generation_notes"],
    )

    return MealPlanResponse(
        plan_id=raw["plan_id"],
        days=day_plans,
        summary=summary,
    )


@router.get(
    "/current",
    response_model=MealPlanResponse,
    summary="Get current meal plan",
    description="Retrieve the most recently generated meal plan for the current user",
)
def get_current_plan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    planner: MealPlanner = Depends(get_meal_planner),
):
    meal_plan = planner.get_current_plan(user_id=current_user.id, db=db)
    if not meal_plan:
        raise HTTPException(status_code=404, detail="No meal plan found. Generate one first.")

    raw = meal_plan.plan_data

    # Map raw dicts → Pydantic response models
    day_plans = []
    for d in raw["days"]:
        meals = [
            MealSlot(
                meal_type=m.get("meal_type", "meal"),
                food_name=m.get("food_name", ""),
                food_description=m.get("food_description", ""),
                cuisine_type=m.get("cuisine_type", ""),
                calories=m.get("food_calories_per_serving", 0),
                ingredients=m.get("food_ingredients", ""),
                health_benefits=m.get("food_health_benefits", ""),
                cooking_method=m.get("cooking_method", ""),
                condition_safe=m.get("condition_safe", True),
                similarity_score=m.get("similarity_score", 0.0),
            )
            for m in d["meals"]
        ]
        day_plans.append(
            DayPlan(
                day=d["day"],
                day_name=d["day_name"],
                meals=meals,
                total_calories=d["total_calories"],
                daily_notes=d["daily_notes"],
            )
        )

    s = raw["summary"]
    summary = MealPlanSummary(
        total_days=s["total_days"],
        avg_daily_calories=s["avg_daily_calories"],
        cuisines_included=s["cuisines_included"],
        conditions_applied=s["conditions_applied"],
        generation_notes=s["generation_notes"],
    )

    return MealPlanResponse(
        plan_id=raw["plan_id"],
        days=day_plans,
        summary=summary,
    )


@router.get(
    "/day/{day_name}",
    response_model=DayPlan,
    summary="Get specific day from current meal plan",
    description="Retrieve details for a specific day (e.g., Monday, Tuesday) from the current meal plan",
)
def get_day_plan(
    day_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    planner: MealPlanner = Depends(get_meal_planner),
):
    meal_plan = planner.get_current_plan(user_id=current_user.id, db=db)
    if not meal_plan:
        raise HTTPException(status_code=404, detail="No meal plan found. Generate one first.")

    raw = meal_plan.plan_data

    # Find the requested day
    day_data = next((d for d in raw["days"] if d["day_name"].lower() == day_name.lower()), None)
    if not day_data:
        raise HTTPException(status_code=404, detail=f"Day '{day_name}' not found in meal plan.")

    # Map meals to Pydantic models
    meals = [
        MealSlot(
            meal_type=m.get("meal_type", "meal"),
            food_name=m.get("food_name", ""),
            food_description=m.get("food_description", ""),
            cuisine_type=m.get("cuisine_type", ""),
            calories=m.get("food_calories_per_serving", 0),
            ingredients=m.get("food_ingredients", ""),
            health_benefits=m.get("food_health_benefits", ""),
            cooking_method=m.get("cooking_method", ""),
            condition_safe=m.get("condition_safe", True),
            similarity_score=m.get("similarity_score", 0.0),
        )
        for m in day_data["meals"]
    ]

    return DayPlan(
        day=day_data["day"],
        day_name=day_data["day_name"],
        meals=meals,
        total_calories=day_data["total_calories"],
        daily_notes=day_data["daily_notes"],
    )


@router.delete(
    "",
    summary="Delete current meal plan",
    description="Delete the current meal plan for the user",
)
def delete_plan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    planner: MealPlanner = Depends(get_meal_planner),
):
    deleted = planner.delete_plan(user_id=current_user.id, db=db)
    if not deleted:
        raise HTTPException(status_code=404, detail="No meal plan found to delete.")
    return {"message": "Meal plan deleted successfully"}
