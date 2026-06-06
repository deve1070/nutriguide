"""
Shared bot service used by both Telegram and WhatsApp bots.

Responsibilities:
- Get or create bot users (auto-registers new platform users)
- Load their health profile for personalized responses
- Call the RAG engine with conversation context
- Format responses for each platform
- Persist conversation history (last 5 exchanges)
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from backend.core.vector_store import get_vector_store
from backend.models.bot_user import BotUser
from backend.models.health_profile import HealthProfile
from backend.models.user import User
from backend.services.condition_filter import get_condition_filter
from backend.services.llm_client import get_llm_client
from backend.services.rag_engine import RAGEngine

MAX_HISTORY = 5  # conversation turns to keep


def get_or_create_bot_user(
    db: Session,
    platform: str,
    platform_user_id: str,
    platform_username: Optional[str] = None,
    display_name: Optional[str] = None,
) -> BotUser:
    """
    Find existing bot user or auto-create a NutriGuide account for them.
    New users get a welcome message and empty health profile.
    """
    bot_user = (
        db.query(BotUser)
        .filter(
            BotUser.platform == platform,
            BotUser.platform_user_id == str(platform_user_id),
        )
        .first()
    )

    if bot_user:
        # Update last active
        bot_user.last_active = datetime.now(timezone.utc)
        db.commit()
        return bot_user

    # Auto-create a NutriGuide account
    name = display_name or platform_username or f"{platform}_user_{platform_user_id}"
    email = f"{platform}_{platform_user_id}@bot.nutriguide.local"

    # Check if user with this email already exists (shouldn't, but be safe)
    existing_user = db.query(User).filter(User.email == email).first()
    if not existing_user:
        user = User(
            email=email,
            full_name=name,
            hashed_password=f"bot:{platform}:{platform_user_id}",
            is_active=True,
        )
        db.add(user)
        db.flush()

        profile = HealthProfile(user_id=user.id)
        db.add(profile)
        db.flush()
    else:
        user = existing_user

    bot_user = BotUser(
        platform=platform,
        platform_user_id=str(platform_user_id),
        platform_username=platform_username,
        nutriguide_user_id=user.id,
        conversation_history=[],
    )
    db.add(bot_user)
    db.commit()
    db.refresh(bot_user)
    return bot_user


def process_message(
    db: Session,
    bot_user: BotUser,
    message: str,
) -> str:
    """
    Core message handler — runs RAG with the user's health profile.
    Returns a plain-text response suitable for any messaging platform.
    """
    # Handle commands
    lower = message.strip().lower()

    if lower in ["/start", "hi", "hello", "hey", "start"]:
        return _welcome_message(bot_user)

    if lower in ["/help", "help"]:
        return _help_message()

    if lower in ["/profile", "profile", "my profile"]:
        return _profile_summary(db, bot_user)

    if lower in ["/mealplan", "meal plan", "generate meal plan", "weekly plan"]:
        return _quick_meal_plan(db, bot_user)

    # Everything else → RAG
    return _rag_response(db, bot_user, message)


def _rag_response(db: Session, bot_user: BotUser, query: str) -> str:
    """Call RAG engine with health context and return formatted response"""
    profile = (
        db.query(HealthProfile)
        .filter(HealthProfile.user_id == bot_user.nutriguide_user_id)
        .first()
    )

    conditions = profile.conditions if profile else []
    dietary_restrictions = profile.dietary_restrictions if profile else []
    allergies = profile.allergies if profile else []
    preferred_cuisines = profile.preferred_cuisines if profile else []
    calorie_target = profile.daily_calorie_target if profile else None

    engine = RAGEngine(
        vector_store=get_vector_store(),
        llm_client=get_llm_client(),
        condition_filter=get_condition_filter(),
    )

    result = engine.chat(
        query=query,
        conditions=conditions,
        dietary_restrictions=dietary_restrictions,
        allergies=allergies,
        preferred_cuisines=preferred_cuisines,
        max_calories=calorie_target,
        n_results=3,
    )

    response_text = result["response"]

    # Append top food results in a clean format
    sources = result.get("sources", [])
    if sources:
        response_text += "\n\n🍽 *Top matches:*"
        for i, food in enumerate(sources[:3], 1):
            cal = food.get("food_calories_per_serving", "?")
            cuisine = food.get("cuisine_type", "")
            score = int(food.get("similarity_score", 0) * 100)
            response_text += (
                f"\n{i}. *{food['food_name']}* — {cuisine} | {cal} cal | {score}% match"
            )

    # Add condition notes if any
    notes = result.get("condition_notes", [])
    if notes:
        response_text += f"\n\n🩺 _{notes[0]}_"

    # Save to conversation history
    _update_history(db, bot_user, query, response_text)

    return response_text


def _update_history(db: Session, bot_user: BotUser, user_msg: str, bot_msg: str):
    history = list(bot_user.conversation_history or [])
    history.append({"role": "user", "content": user_msg})
    history.append(
        {"role": "assistant", "content": bot_msg[:200]}
    )  # truncate for storage
    bot_user.conversation_history = history[-MAX_HISTORY * 2 :]
    db.commit()


def _welcome_message(bot_user: BotUser) -> str:
    name = bot_user.platform_username or "there"
    return (
        f"👋 Hello {name}! I'm *NutriGuide* — your clinical nutrition assistant.\n\n"
        "I give personalized food recommendations based on your health conditions.\n\n"
        "Just tell me what you're looking for:\n"
        "• _'I want something light and healthy'_\n"
        "• _'High protein breakfast ideas'_\n"
        "• _'Food safe for diabetes'_\n\n"
        "Commands:\n"
        "/profile — see your health profile\n"
        "/mealplan — get a quick meal suggestion\n"
        "/help — show this menu"
    )


def _help_message() -> str:
    return (
        "🥗 *NutriGuide Help*\n\n"
        "Just type any food question in natural language.\n\n"
        "*Example queries:*\n"
        "• 'What should I eat for dinner?'\n"
        "• 'Low calorie Italian food'\n"
        "• 'Breakfast for someone with PCOS'\n"
        "• 'Healthy Ethiopian dishes'\n\n"
        "*Commands:*\n"
        "/profile — your health conditions\n"
        "/mealplan — quick meal suggestion\n"
        "/start — restart the bot\n\n"
        "💡 _The more specific you are, the better the recommendations._"
    )


def _profile_summary(db: Session, bot_user: BotUser) -> str:
    profile = (
        db.query(HealthProfile)
        .filter(HealthProfile.user_id == bot_user.nutriguide_user_id)
        .first()
    )

    if not profile or not (profile.conditions or profile.daily_calorie_target):
        return (
            "📋 Your health profile is empty.\n\n"
            "Visit the NutriGuide web app to set up your conditions, "
            "allergies, and nutrition goals for personalized recommendations."
        )

    lines = ["📋 *Your Health Profile*\n"]
    if profile.conditions:
        lines.append(
            f"🩺 Conditions: {', '.join(profile.conditions).replace('_', ' ')}"
        )
    if profile.dietary_restrictions:
        lines.append(f"🌿 Diet: {', '.join(profile.dietary_restrictions)}")
    if profile.allergies:
        lines.append(f"⚠️ Allergies: {', '.join(profile.allergies)}")
    if profile.preferred_cuisines:
        lines.append(f"🌍 Cuisines: {', '.join(profile.preferred_cuisines)}")
    if profile.daily_calorie_target:
        lines.append(f"🔥 Calorie target: {profile.daily_calorie_target} cal/day")
    if profile.primary_goal:
        lines.append(f"🎯 Goal: {profile.primary_goal.replace('_', ' ')}")

    lines.append("\n_All recommendations are personalised to this profile._")
    return "\n".join(lines)


def _quick_meal_plan(db: Session, bot_user: BotUser) -> str:
    """Generate a quick 3-meal suggestion for today"""
    return _rag_response(
        db, bot_user, "Give me breakfast, lunch and dinner suggestions for today"
    )
