from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base

if TYPE_CHECKING:
    from backend.models.user import User


class HealthProfile(Base):
    __tablename__ = "health_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    # ── Physical stats ────────────────────────────────
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    weight_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    height_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # ── Conditions (stored as JSON list) ─────────────
    # e.g. ["diabetes_type2", "hypertension"]
    conditions: Mapped[list] = mapped_column(JSON, default=list)

    # ── Dietary restrictions ──────────────────────────
    # e.g. ["gluten_free", "lactose_intolerant", "vegan"]
    dietary_restrictions: Mapped[list] = mapped_column(JSON, default=list)

    # ── Allergies ─────────────────────────────────────
    # e.g. ["peanuts", "shellfish"]
    allergies: Mapped[list] = mapped_column(JSON, default=list)

    # ── Cuisine preferences ───────────────────────────
    # e.g. ["Ethiopian", "Italian", "Mediterranean"]
    preferred_cuisines: Mapped[list] = mapped_column(JSON, default=list)

    # ── Nutrition goals ───────────────────────────────
    daily_calorie_target: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # e.g. "weight_loss", "muscle_gain", "maintenance", "manage_condition"
    primary_goal: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # ── Activity level ────────────────────────────────
    # sedentary | lightly_active | moderately_active | very_active
    activity_level: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="health_profile")

    def __repr__(self) -> str:
        return f"<HealthProfile user_id={self.user_id} conditions={self.conditions}>"
