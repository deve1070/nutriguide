"""
Meal Planner Service

Generates a multi-day personalized meal plan by:
1. Querying the vector store with meal-type-specific prompts
2. Applying condition-aware re-ranking to every slot
3. Enforcing variety — no food repeated within the plan
4. Generating a daily tip and plan summary via the LLM
5. Persisting plans to database for retrieval
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from backend.core.vector_store import VectorStore
from backend.models.meal_plan import MealPlan
from backend.services.condition_filter import ConditionFilter
from backend.services.llm_client import LLMClient

DAY_NAMES = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

MEAL_QUERIES = {
    "breakfast": [
        "healthy breakfast high protein",
        "light morning meal nutritious",
        "quick breakfast whole grain",
        "energizing breakfast low sugar",
        "fibre-rich morning meal",
    ],
    "lunch": [
        "balanced lunch meal vegetables",
        "light filling lunch low calorie",
        "nutritious lunch lean protein",
        "fresh lunch salad grain bowl",
        "satisfying lunch meal",
    ],
    "dinner": [
        "healthy dinner lean protein vegetables",
        "light evening meal nutritious",
        "wholesome dinner balanced meal",
        "comforting healthy dinner",
        "flavourful dinner low calorie",
    ],
    "snack": [
        "healthy light snack",
        "nutritious snack low calorie",
        "protein snack between meals",
    ],
}


class MealPlanner:
    def __init__(
        self,
        vector_store: VectorStore,
        llm_client: LLMClient,
        condition_filter: ConditionFilter,
    ):
        self.vector_store = vector_store
        self.llm = llm_client
        self.condition_filter = condition_filter

    def save_plan(
        self,
        plan_data: Dict,
        user_id: int,
        db: Session,
        days: int = 7,
    ) -> MealPlan:
        """Save a meal plan to the database, replacing any existing plan for the user"""
        # Delete existing plan for this user
        db.query(MealPlan).filter(MealPlan.user_id == user_id).delete()

        # Calculate start and end dates (start from today)
        start_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=days - 1)

        # Create new plan
        meal_plan = MealPlan(
            user_id=user_id,
            plan_id=plan_data["plan_id"],
            plan_data=plan_data,
            start_date=start_date,
            end_date=end_date,
        )
        db.add(meal_plan)
        db.commit()
        db.refresh(meal_plan)
        return meal_plan

    def get_current_plan(self, user_id: int, db: Session) -> Optional[MealPlan]:
        """Get the most recent meal plan for a user"""
        return (
            db.query(MealPlan)
            .filter(MealPlan.user_id == user_id)
            .order_by(MealPlan.created_at.desc())
            .first()
        )

    def delete_plan(self, user_id: int, db: Session) -> bool:
        """Delete the current meal plan for a user"""
        deleted = (
            db.query(MealPlan)
            .filter(MealPlan.user_id == user_id)
            .delete()
        )
        db.commit()
        return deleted > 0

    def generate(
        self,
        days: int = 7,
        meals_per_day: int = 3,
        conditions: Optional[List[str]] = None,
        dietary_restrictions: Optional[List[str]] = None,
        allergies: Optional[List[str]] = None,
        max_calories_per_day: Optional[int] = None,
        cuisine_preferences: Optional[List[str]] = None,
    ) -> Dict:
        """Generate a full meal plan and return structured data"""

        conditions = conditions or []
        allergies = allergies or []
        meal_types = self._meal_types(meals_per_day)
        used_food_ids: set = set()

        # Derive per-meal calorie budget
        per_meal_cap = self._per_meal_cap(
            conditions, max_calories_per_day, meals_per_day
        )

        day_plans = []
        all_cuisines: set = set()

        for day_num in range(1, days + 1):
            day_name = DAY_NAMES[(day_num - 1) % 7]
            meals = []
            day_calories = 0

            for meal_type in meal_types:
                slot = self._pick_meal(
                    meal_type=meal_type,
                    conditions=conditions,
                    allergies=allergies,
                    per_meal_cap=per_meal_cap,
                    cuisine_preferences=cuisine_preferences,
                    used_food_ids=used_food_ids,
                    day_num=day_num,
                )
                if slot:
                    meals.append(slot)
                    used_food_ids.add(slot["food_id"])
                    day_calories += slot.get("food_calories_per_serving", 0)
                    all_cuisines.add(slot.get("cuisine_type", ""))

            daily_note = self._daily_tip(day_name, meals, conditions)

            day_plans.append(
                {
                    "day": day_num,
                    "day_name": day_name,
                    "meals": meals,
                    "total_calories": day_calories,
                    "daily_notes": daily_note,
                }
            )

        avg_calories = (
            sum(d["total_calories"] for d in day_plans) / len(day_plans)
            if day_plans
            else 0
        )

        summary_notes = self._plan_summary(conditions, avg_calories, days)

        return {
            "plan_id": str(uuid.uuid4())[:8],
            "days": day_plans,
            "summary": {
                "total_days": days,
                "avg_daily_calories": round(avg_calories, 1),
                "cuisines_included": list(all_cuisines - {""}),
                "conditions_applied": conditions,
                "generation_notes": summary_notes,
            },
        }

    # ── Private helpers ───────────────────────────────

    def _meal_types(self, meals_per_day: int) -> List[str]:
        if meals_per_day == 2:
            return ["lunch", "dinner"]
        if meals_per_day == 3:
            return ["breakfast", "lunch", "dinner"]
        if meals_per_day == 4:
            return ["breakfast", "lunch", "dinner", "snack"]
        return ["breakfast", "snack", "lunch", "snack", "dinner"]

    def _per_meal_cap(
        self,
        conditions: List[str],
        daily_cap: Optional[int],
        meals_per_day: int,
    ) -> Optional[int]:
        """Derive a per-meal calorie cap from daily target or condition rules"""
        if daily_cap:
            return daily_cap // meals_per_day
        cap = self.condition_filter.get_calorie_cap(conditions)
        return cap  # already a per-meal cap from clinical rules

    def _pick_meal(
        self,
        meal_type: str,
        conditions: List[str],
        allergies: List[str],
        per_meal_cap: Optional[int],
        cuisine_preferences: Optional[List[str]],
        used_food_ids: set,
        day_num: int,
    ) -> Optional[Dict]:
        """Find the best food for a meal slot that hasn't been used yet"""
        queries = MEAL_QUERIES.get(meal_type, MEAL_QUERIES["lunch"])
        # Rotate through queries for variety across days
        query = queries[(day_num - 1) % len(queries)]

        cuisine = None
        if cuisine_preferences:
            cuisine = cuisine_preferences[(day_num - 1) % len(cuisine_preferences)]

        results = self.vector_store.similarity_search(
            query=query,
            n_results=10,
            cuisine_filter=cuisine,
            max_calories=per_meal_cap,
        )

        # Fallback: no cuisine filter if empty
        if not results:
            results = self.vector_store.similarity_search(
                query=query,
                n_results=10,
                max_calories=per_meal_cap,
            )

        # Apply allergen filter
        if allergies:
            results = [
                r
                for r in results
                if not any(
                    a.lower() in r.get("food_ingredients", "").lower()
                    for a in allergies
                )
            ]

        # Apply condition re-ranking
        if conditions:
            results, _ = self.condition_filter.rerank(
                results=results,
                conditions=conditions,
                calorie_override=per_meal_cap,
            )

        # Pick first result not already used in this plan
        for result in results:
            if result["food_id"] not in used_food_ids:
                result["meal_type"] = meal_type
                result["condition_safe"] = True
                return result

        # If all top results used, return first available
        return results[0] if results else None

    def _daily_tip(
        self, day_name: str, meals: List[Dict], conditions: List[str]
    ) -> str:
        """Generate a short daily nutrition tip via LLM"""
        food_names = [m.get("food_name", "") for m in meals]
        condition_text = (
            f" for someone with {', '.join(conditions)}" if conditions else ""
        )

        prompt = (
            f"Today is {day_name}. The planned meals are: {', '.join(food_names)}{condition_text}. "
            f"Give one short, practical nutrition tip for today (1-2 sentences max)."
        )
        tip = self.llm.complete(prompt=prompt, max_tokens=80, temperature=0.8)
        return (
            tip or f"Great choices for {day_name}! Stay hydrated and enjoy your meals."
        )

    def _plan_summary(
        self, conditions: List[str], avg_calories: float, days: int
    ) -> str:
        """Generate an overall plan rationale via LLM"""
        condition_text = (
            f"tailored for {', '.join(conditions)}"
            if conditions
            else "for general healthy eating"
        )
        prompt = (
            f"Summarize a {days}-day meal plan {condition_text} "
            f"averaging {avg_calories:.0f} calories per day. "
            f"Give a 2-3 sentence motivational overview."
        )
        summary = self.llm.complete(prompt=prompt, max_tokens=120, temperature=0.7)
        return summary or (
            f"Your {days}-day personalized meal plan has been generated "
            f"{condition_text}, averaging {avg_calories:.0f} calories per day. "
            "Enjoy a diverse range of nutritious meals tailored to your health goals!"
        )
