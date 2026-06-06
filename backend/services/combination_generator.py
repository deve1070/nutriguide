"""
AI Food Combination Generator

Triggered when:
  - Fewer than MIN_RESULTS remain after condition filtering, OR
  - The best similarity score is below SCORE_THRESHOLD

Instead of showing poor matches, the LLM generates a safe, personalized
food combination using ingredients known to be safe for the user's conditions.

The generated result is flagged with is_generated=True so the frontend
can display it differently (✨ Custom suggestion vs 📊 From database).
"""

from typing import Dict, List, Optional

from backend.core.clinical_rules import CLINICAL_RULES
from backend.services.llm_client import LLMClient

# Thresholds that trigger combination mode
MIN_RESULTS = 2  # fewer than this many results after filtering → trigger
SCORE_THRESHOLD = 0.45  # best score below this → trigger

# Safe ingredient pools per condition — seeds the LLM prompt
SAFE_INGREDIENTS: dict[str, list[str]] = {
    "diabetes_type2": [
        "leafy greens",
        "broccoli",
        "cauliflower",
        "lentils",
        "chickpeas",
        "Greek yogurt",
        "berries",
        "oats",
        "quinoa",
        "nuts",
        "seeds",
        "olive oil",
        "avocado",
        "salmon",
        "eggs",
        "dark chocolate (70%+)",
        "cinnamon",
        "turmeric",
        "ginger",
    ],
    "hypertension": [
        "banana",
        "beets",
        "leafy greens",
        "oats",
        "berries",
        "pomegranate",
        "garlic",
        "olive oil",
        "salmon",
        "flaxseed",
        "potassium-rich vegetables",
        "unsalted nuts",
        "lemon",
        "herbs",
    ],
    "chronic_kidney_disease": [
        "white rice",
        "pasta",
        "apple",
        "berries",
        "cabbage",
        "cauliflower",
        "egg whites",
        "lean chicken",
        "olive oil",
        "onion",
        "garlic",
        "herbs",
    ],
    "pcos": [
        "leafy greens",
        "berries",
        "salmon",
        "turmeric",
        "ginger",
        "lentils",
        "quinoa",
        "avocado",
        "nuts",
        "seeds",
        "olive oil",
        "lean chicken",
        "tofu",
        "cinnamon",
        "dark chocolate",
    ],
    "celiac": [
        "rice",
        "quinoa",
        "potatoes",
        "corn",
        "sweet potato",
        "lentils",
        "beans",
        "meat",
        "fish",
        "eggs",
        "nuts",
        "most fruits and vegetables",
        "gluten-free oats",
    ],
    "lactose_intolerant": [
        "almond milk",
        "oat milk",
        "coconut milk",
        "all fruits",
        "all vegetables",
        "meat",
        "fish",
        "eggs",
        "nuts",
        "seeds",
        "lentils",
        "rice",
        "olive oil",
    ],
    "heart_disease": [
        "salmon",
        "sardines",
        "oats",
        "berries",
        "leafy greens",
        "olive oil",
        "avocado",
        "nuts",
        "legumes",
        "whole grains",
        "garlic",
        "tomatoes",
        "dark chocolate",
    ],
    "obesity": [
        "leafy greens",
        "cucumber",
        "tomato",
        "berries",
        "lean protein",
        "eggs",
        "Greek yogurt",
        "legumes",
        "broth-based soups",
        "steamed vegetables",
        "grilled chicken",
        "fish",
    ],
}

# Generic safe ingredients when no specific condition match
GENERAL_SAFE = [
    "vegetables",
    "fruits",
    "lean protein",
    "whole grains",
    "legumes",
    "olive oil",
    "herbs",
    "spices",
]


class CombinationGenerator:
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def should_trigger(
        self,
        results: List[Dict],
        conditions: List[str],
    ) -> bool:
        """
        Decide whether to generate a custom combination.
        Triggers if results are too few or quality is too low after
        condition filtering AND the user has health conditions.
        """
        if not conditions:
            return False  # no conditions → standard results are fine

        if len(results) < MIN_RESULTS:
            return True

        if (
            results
            and results[0].get("condition_score", results[0].get("similarity_score", 0))
            < SCORE_THRESHOLD
        ):
            return True

        return False

    def generate(
        self,
        query: str,
        conditions: List[str],
        dietary_restrictions: List[str],
        allergies: List[str],
        preferred_cuisines: List[str],
        max_calories: Optional[int] = None,
    ) -> Optional[Dict]:
        """
        Generate a safe food combination tailored to the user's conditions.
        Returns a dict in the same shape as a FoodResult, with is_generated=True.
        """
        safe_ingredients = self._get_safe_ingredients(conditions)
        condition_notes = self._get_condition_notes(conditions)
        cuisine_hint = (
            f" in {preferred_cuisines[0]} style" if preferred_cuisines else ""
        )
        calorie_hint = f" under {max_calories} calories" if max_calories else ""
        restriction_hint = (
            f" Dietary restrictions: {', '.join(dietary_restrictions)}."
            if dietary_restrictions
            else ""
        )
        allergy_hint = f" Must avoid: {', '.join(allergies)}." if allergies else ""

        prompt = f"""A user with {", ".join(conditions).replace("_", " ")} is asking for: "{query}"{cuisine_hint}{calorie_hint}.

Their database search found no safe matching foods after applying clinical nutrition filters.

Create ONE safe, practical food combination using these condition-safe ingredients:
{", ".join(safe_ingredients[:15])}

{restriction_hint}{allergy_hint}

Respond ONLY with a JSON object in this exact format (no markdown, no explanation):
{{
  "food_name": "Short descriptive name (3-5 words)",
  "food_description": "One sentence describing the dish and why it suits the user's request",
  "cuisine_type": "Cuisine type (e.g. Mediterranean, Ethiopian, Asian Fusion)",
  "food_calories_per_serving": <integer estimate>,
  "food_ingredients": ["ingredient 1", "ingredient 2", "ingredient 3", "ingredient 4", "ingredient 5"],
  "food_health_benefits": "One sentence on why this is safe and beneficial for their condition",
  "cooking_method": "Simple cooking method (e.g. Raw, Grilled, Steamed, Stir-fried)",
  "taste_profile": "2-3 taste descriptors (e.g. Light, fresh, slightly sweet)",
  "why_safe": "One sentence explaining the clinical reason this works for their condition"
}}"""

        raw = self.llm.complete(
            prompt=prompt,
            system=(
                "You are a clinical nutritionist creating safe food combinations. "
                "Respond only with valid JSON, no other text."
            ),
            max_tokens=400,
            temperature=0.8,
        )

        if not raw:
            return self._fallback_combination(query, conditions, safe_ingredients)

        return self._parse_response(raw, conditions, condition_notes)

    def _parse_response(
        self, raw: str, conditions: List[str], condition_notes: List[str]
    ) -> Optional[Dict]:
        """Parse LLM JSON response into a FoodResult-shaped dict"""
        import json

        # Strip markdown fences if present
        clean = raw.strip().replace("```json", "").replace("```", "").strip()

        try:
            data = json.loads(clean)
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            import re

            match = re.search(r"\{.*\}", clean, re.DOTALL)
            if not match:
                return None
            try:
                data = json.loads(match.group())
            except Exception:
                return None

        # Validate required fields
        if not data.get("food_name"):
            return None

        return {
            "food_id": f"generated_{hash(data['food_name']) % 100000}",
            "food_name": data.get("food_name", "Custom Combination"),
            "food_description": data.get("food_description", ""),
            "cuisine_type": data.get("cuisine_type", "Custom"),
            "food_calories_per_serving": int(
                data.get("food_calories_per_serving", 300)
            ),
            "food_ingredients": ", ".join(data.get("food_ingredients", [])),
            "food_health_benefits": data.get("food_health_benefits", ""),
            "cooking_method": data.get("cooking_method", ""),
            "taste_profile": data.get("taste_profile", ""),
            "similarity_score": 1.0,  # it's a direct match to the query
            "condition_score": 1.0,
            "is_generated": True,
            "why_safe": data.get("why_safe", ""),
            "condition_notes": condition_notes,
        }

    def _fallback_combination(
        self, query: str, conditions: List[str], safe_ingredients: List[str]
    ) -> Dict:
        """Return a hardcoded safe fallback when LLM fails"""
        condition_str = (
            conditions[0].replace("_", " ") if conditions else "your condition"
        )
        top_ingredients = safe_ingredients[:5]
        return {
            "food_id": "generated_fallback",
            "food_name": f"Safe {condition_str.title()} Bowl",
            "food_description": f"A simple, safe combination of {', '.join(top_ingredients[:3])}.",
            "cuisine_type": "Health Food",
            "food_calories_per_serving": 280,
            "food_ingredients": ", ".join(top_ingredients),
            "food_health_benefits": f"Ingredients selected for safety with {condition_str}.",
            "cooking_method": "Mixed",
            "taste_profile": "Light, nutritious",
            "similarity_score": 1.0,
            "condition_score": 1.0,
            "is_generated": True,
            "why_safe": f"All ingredients are safe for {condition_str}.",
            "condition_notes": [],
        }

    def _get_safe_ingredients(self, conditions: List[str]) -> List[str]:
        """Merge safe ingredient lists for all user conditions"""
        ingredients = set()
        for condition in conditions:
            ingredients.update(SAFE_INGREDIENTS.get(condition, GENERAL_SAFE))
        return list(ingredients) if ingredients else GENERAL_SAFE

    def _get_condition_notes(self, conditions: List[str]) -> List[str]:
        notes = []
        for condition in conditions:
            rule = CLINICAL_RULES.get(condition)
            if rule:
                notes.append(rule["notes"])
        return notes


# ── Singleton ─────────────────────────────────────────
_generator: Optional[CombinationGenerator] = None


def get_combination_generator() -> CombinationGenerator:
    global _generator
    if _generator is None:
        from backend.services.llm_client import get_llm_client

        _generator = CombinationGenerator(get_llm_client())
    return _generator
