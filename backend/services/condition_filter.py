"""
Condition-aware food re-ranking.

Takes raw similarity search results and re-scores them based on
the user's health conditions using clinical rules from clinical_rules.py.

Scoring logic:
  final_score = similarity_score
              + sum(boost_score for each boost keyword found)
              - sum(penalty_score for each penalty keyword found)

Foods with avoid_keywords are removed from results entirely.
Results are then re-sorted by final_score descending.
"""

from typing import Dict, List, Optional

from backend.core.clinical_rules import ConditionRule, get_rule


class ConditionFilter:
    def rerank(
        self,
        results: List[Dict],
        conditions: List[str],
        calorie_override: Optional[int] = None,
    ) -> tuple[List[Dict], List[str]]:
        """
        Re-rank and filter results based on health conditions.

        Returns:
            - reranked list of food results (with condition_score added)
            - list of condition notes to surface to the user
        """
        if not conditions or not results:
            return results, []

        notes: List[str] = []
        active_rules: List[ConditionRule] = []

        for condition in conditions:
            rule = get_rule(condition)
            if rule:
                active_rules.append(rule)
                notes.append(rule["notes"])

        if not active_rules:
            return results, []

        # Determine effective calorie cap
        calorie_caps = [
            r["calorie_cap"] for r in active_rules if r["calorie_cap"] is not None
        ]
        effective_cap = calorie_override or (
            min(calorie_caps) if calorie_caps else None
        )

        scored: List[Dict] = []

        for food in results:
            # Build a single searchable text blob from the food item
            food_text = " ".join(
                [
                    food.get("food_name", ""),
                    food.get("food_description", ""),
                    food.get("food_ingredients", ""),
                    food.get("food_health_benefits", ""),
                    food.get("taste_profile", ""),
                    food.get("cooking_method", ""),
                ]
            ).lower()

            # Hard filter: calorie cap
            calories = food.get("food_calories_per_serving", 0)
            if effective_cap and calories > effective_cap:
                continue

            # Hard filter: avoid keywords across all conditions
            should_avoid = False
            for rule in active_rules:
                for kw in rule["avoid_keywords"]:
                    if kw.lower() in food_text:
                        should_avoid = True
                        break
                if should_avoid:
                    break
            if should_avoid:
                continue

            # Soft scoring: boost and penalty keywords
            condition_score = food["similarity_score"]

            for rule in active_rules:
                for kw in rule["boost_keywords"]:
                    if kw.lower() in food_text:
                        condition_score += rule["boost_score"]
                        break  # one boost per rule max to avoid stacking

                for kw in rule["penalty_keywords"]:
                    if kw.lower() in food_text:
                        condition_score -= rule["penalty_score"]
                        break  # one penalty per rule max

            # Clamp score to [0, 1]
            condition_score = max(0.0, min(1.0, round(condition_score, 4)))

            food_copy = food.copy()
            food_copy["condition_score"] = condition_score
            food_copy["original_similarity"] = food["similarity_score"]
            scored.append(food_copy)

        # Sort by condition score descending
        scored.sort(key=lambda x: x["condition_score"], reverse=True)

        # Deduplicate notes (multiple conditions may share similar notes)
        unique_notes = list(dict.fromkeys(notes))

        return scored, unique_notes

    def get_calorie_cap(
        self, conditions: List[str], override: Optional[int] = None
    ) -> Optional[int]:
        """Return the most restrictive calorie cap for the given conditions"""
        if override:
            return override
        caps = []
        for condition in conditions:
            rule = get_rule(condition)
            if rule and rule["calorie_cap"]:
                caps.append(rule["calorie_cap"])
        return min(caps) if caps else None


# ── Singleton ─────────────────────────────────────────
_condition_filter: Optional[ConditionFilter] = None


def get_condition_filter() -> ConditionFilter:
    global _condition_filter
    if _condition_filter is None:
        _condition_filter = ConditionFilter()
    return _condition_filter
