from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.core.clinical_rules import CLINICAL_RULES
from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.health_profile import HealthProfile
from backend.models.user import User

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get(
    "/my-profile-summary",
    summary="Get a summary of your health profile and how it affects recommendations",
)
def profile_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = (
        db.query(HealthProfile).filter(HealthProfile.user_id == current_user.id).first()
    )

    if not profile:
        return {
            "message": "No health profile found. Update your profile to get personalised recommendations."
        }

    # Build active clinical notes for the user's conditions
    active_rules = []
    for condition in profile.conditions or []:
        rule = CLINICAL_RULES.get(condition)
        if rule:
            active_rules.append(
                {
                    "condition": condition,
                    "calorie_cap_per_meal": rule["calorie_cap"],
                    "notes": rule["notes"],
                    "foods_prioritized": rule["boost_keywords"][:5],
                    "foods_limited": rule["penalty_keywords"][:5],
                }
            )

    # Calculate BMI if data available
    bmi = None
    bmi_category = None
    if profile.weight_kg and profile.height_cm:
        height_m = profile.height_cm / 100
        bmi = round(profile.weight_kg / (height_m**2), 1)
        if bmi < 18.5:
            bmi_category = "Underweight"
        elif bmi < 25:
            bmi_category = "Normal weight"
        elif bmi < 30:
            bmi_category = "Overweight"
        else:
            bmi_category = "Obese"

    return {
        "user": current_user.full_name,
        "profile_complete": bool(profile.conditions or profile.daily_calorie_target),
        "conditions": profile.conditions,
        "dietary_restrictions": profile.dietary_restrictions,
        "allergies": profile.allergies,
        "preferred_cuisines": profile.preferred_cuisines,
        "daily_calorie_target": profile.daily_calorie_target,
        "primary_goal": profile.primary_goal,
        "bmi": bmi,
        "bmi_category": bmi_category,
        "active_clinical_rules": active_rules,
        "personalisation_active": len(active_rules) > 0,
    }


@router.get(
    "/conditions-guide",
    summary="Get nutrition guidance for all supported health conditions",
)
def conditions_guide():
    """Returns the full clinical rule set — useful for onboarding UI"""
    guide = {}
    for condition, rule in CLINICAL_RULES.items():
        guide[condition] = {
            "notes": rule["notes"],
            "calorie_cap_per_meal": rule["calorie_cap"],
            "prioritized_foods": rule["boost_keywords"][:8],
            "limited_foods": rule["penalty_keywords"][:6],
        }
    return {"conditions": guide}
