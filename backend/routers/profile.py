from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.health_profile import HealthProfile
from backend.models.user import User
from backend.schemas.profile import HealthProfileResponse, HealthProfileUpdate

router = APIRouter(prefix="/profile", tags=["Health Profile"])


@router.get(
    "/me",
    response_model=HealthProfileResponse,
    summary="Get my health profile",
)
def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = (
        db.query(HealthProfile).filter(HealthProfile.user_id == current_user.id).first()
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Health profile not found. This shouldn't happen — contact support.",
        )
    return profile


@router.put(
    "/health",
    response_model=HealthProfileResponse,
    summary="Update my health profile (conditions, allergies, goals, etc.)",
)
def update_health_profile(
    payload: HealthProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = (
        db.query(HealthProfile).filter(HealthProfile.user_id == current_user.id).first()
    )

    if not profile:
        # Shouldn't happen — profile created on register — but handle gracefully
        profile = HealthProfile(user_id=current_user.id)
        db.add(profile)

    # Only update fields that were explicitly provided in the request
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile


@router.get(
    "/conditions",
    summary="List all supported health conditions",
)
def list_supported_conditions():
    """Returns the list of conditions NutriGuide can personalise recommendations for"""
    from backend.schemas.profile import SUPPORTED_CONDITIONS

    return {"conditions": SUPPORTED_CONDITIONS}
