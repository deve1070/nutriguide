from typing import Dict, List, Optional

from backend.core.vector_store import VectorStore
from backend.services.condition_filter import ConditionFilter
from backend.services.llm_client import LLMClient

SYSTEM_PROMPT = """You are NutriGuide, a clinical nutrition assistant. You help people 
find foods that match their health goals and medical conditions.

Rules you must follow:
- Only recommend foods from the retrieved database results provided to you
- Always mention relevant health benefits or cautions for the user's conditions
- Keep responses concise, warm, and practical (3-5 sentences max per recommendation)
- Never invent nutritional facts — only use what is in the context
- If the user has a health condition, prioritize safety in your recommendations
- End with one actionable tip the user can apply immediately"""


class RAGEngine:
    """
    Retrieval-Augmented Generation engine.
    1. Retrieves relevant food items from ChromaDB
    2. Assembles structured context
    3. Generates a personalized response via Groq
    """

    def __init__(
        self,
        vector_store: VectorStore,
        llm_client: LLMClient,
        condition_filter: ConditionFilter,
    ):
        self.vector_store = vector_store
        self.llm = llm_client
        self.condition_filter = condition_filter

    def chat(
        self,
        query: str,
        conditions: Optional[List[str]] = None,
        dietary_restrictions: Optional[List[str]] = None,
        allergies: Optional[List[str]] = None,
        preferred_cuisines: Optional[List[str]] = None,
        max_calories: Optional[int] = None,
        n_results: int = 5,
        conversation_history: Optional[List[dict]] = None,
    ) -> Dict:
        """
        Main entry point — takes a user query + health context,
        returns AI response + the raw search results used.
        """
        # ── Step 1: Retrieve ─────────────────────────
        # Use preferred cuisine as a soft filter if provided
        cuisine_filter = preferred_cuisines[0] if preferred_cuisines else None

        search_results = self.vector_store.similarity_search(
            query=query,
            n_results=n_results,
            cuisine_filter=cuisine_filter,
            max_calories=max_calories,
        )

        # Fallback: retry without filters if no results
        if not search_results and cuisine_filter:
            search_results = self.vector_store.similarity_search(
                query=query,
                n_results=n_results,
                max_calories=max_calories,
            )

        # ── Step 2: Filter allergies client-side ─────
        if allergies and search_results:
            search_results = self._filter_allergens(search_results, allergies)

        # ── Step 3: Condition-aware re-ranking ────────
        condition_notes: List[str] = []
        if conditions and search_results:
            search_results, condition_notes = self.condition_filter.rerank(
                results=search_results,
                conditions=conditions,
                calorie_override=max_calories,
            )

        # ── Step 4: Assemble context ──────────────────
        context = self._build_context(search_results)
        health_context = self._build_health_context(
            conditions, dietary_restrictions, allergies
        )

        # ── Step 5: Generate ─────────────────────────
        prompt = self._build_prompt(query, context, health_context)

        # Build messages with history for multi-turn memory
        messages = []
        if conversation_history:
            # Keep last 10 exchanges (20 messages) to stay within token limits
            messages.extend(conversation_history[-20:])
        messages.append({"role": "user", "content": prompt})

        ai_response = self.llm.complete_with_history(
            messages=messages,
            system=SYSTEM_PROMPT,
            max_tokens=400,
            temperature=0.7,
        )

        if not ai_response or len(ai_response) < 40:
            ai_response = self._fallback_response(query, search_results)

        return {
            "response": ai_response,
            "sources": search_results[:3],
            "total_results_found": len(search_results),
            "condition_notes": condition_notes,
            "filters_applied": {
                "cuisine": cuisine_filter,
                "max_calories": max_calories,
                "conditions": conditions or [],
            },
        }

    def compare(
        self,
        query_a: str,
        query_b: str,
        conditions: Optional[List[str]] = None,
    ) -> Dict:
        """Compare two different food queries side-by-side with AI analysis"""
        results_a = self.vector_store.similarity_search(query_a, n_results=3)
        results_b = self.vector_store.similarity_search(query_b, n_results=3)

        context_a = self._build_context(results_a)
        context_b = self._build_context(results_b)
        health_ctx = self._build_health_context(conditions, [], [])

        prompt = f"""Compare these two food preferences for a user{" with " + ", ".join(conditions) if conditions else ""}.

Query A: "{query_a}"
Retrieved options for A:
{context_a}

Query B: "{query_b}"
Retrieved options for B:
{context_b}

{health_ctx}

Provide a short, practical comparison (4-6 sentences):
- Which option better suits the user's health needs and why
- Key nutritional difference between the two
- Your final recommendation"""

        ai_response = self.llm.complete(
            prompt=prompt, system=SYSTEM_PROMPT, max_tokens=350
        )

        return {
            "comparison": ai_response
            or self._simple_comparison(query_a, query_b, results_a, results_b),
            "query_a": {"query": query_a, "results": results_a},
            "query_b": {"query": query_b, "results": results_b},
        }

    # ── Private helpers ───────────────────────────────

    def _build_context(self, results: List[Dict]) -> str:
        if not results:
            return "No matching food items found in the database."

        lines = []
        for i, r in enumerate(results[:3], 1):
            lines.append(f"Option {i}: {r['food_name']}")
            lines.append(f"  Description: {r['food_description']}")
            lines.append(f"  Cuisine: {r['cuisine_type']}")
            lines.append(f"  Calories: {r['food_calories_per_serving']} per serving")
            if r.get("food_ingredients"):
                lines.append(f"  Ingredients: {r['food_ingredients']}")
            if r.get("food_health_benefits"):
                lines.append(f"  Health benefits: {r['food_health_benefits']}")
            if r.get("taste_profile"):
                lines.append(f"  Taste profile: {r['taste_profile']}")
            lines.append(f"  Match score: {r['similarity_score'] * 100:.1f}%")
            lines.append("")
        return "\n".join(lines)

    def _build_health_context(
        self,
        conditions: Optional[List[str]],
        dietary_restrictions: Optional[List[str]],
        allergies: Optional[List[str]],
    ) -> str:
        parts = []
        if conditions:
            parts.append(f"User health conditions: {', '.join(conditions)}")
        if dietary_restrictions:
            parts.append(f"Dietary restrictions: {', '.join(dietary_restrictions)}")
        if allergies:
            parts.append(f"Allergies to avoid: {', '.join(allergies)}")
        return "\n".join(parts) if parts else "No specific health conditions provided."

    def _build_prompt(self, query: str, context: str, health_context: str) -> str:
        return f"""User request: "{query}"

{health_context}

Retrieved food options from the database:
{context}

Based on the retrieved options and the user's health profile, provide a personalized food recommendation response."""

    def _filter_allergens(
        self, results: List[Dict], allergies: List[str]
    ) -> List[Dict]:
        """Remove results that contain allergens in their ingredients"""
        safe = []
        for r in results:
            ingredients_lower = r.get("food_ingredients", "").lower()
            has_allergen = any(
                allergen.lower() in ingredients_lower for allergen in allergies
            )
            if not has_allergen:
                safe.append(r)
        return safe

    def _fallback_response(self, query: str, results: List[Dict]) -> str:
        """Plain-text fallback when LLM is unavailable"""
        if not results:
            return (
                "I couldn't find food items matching your request. "
                "Try different keywords like a cuisine type, ingredient, or meal description."
            )
        top = results[0]
        response = (
            f"Based on your request for '{query}', I recommend **{top['food_name']}**. "
            f"It's a {top['cuisine_type']} dish with {top['food_calories_per_serving']} "
            f"calories per serving."
        )
        if len(results) > 1:
            response += f" You might also enjoy **{results[1]['food_name']}** as an alternative."
        return response

    def _simple_comparison(
        self, query_a: str, query_b: str, results_a: List[Dict], results_b: List[Dict]
    ) -> str:
        if not results_a and not results_b:
            return "No results found for either query."
        if not results_a:
            return f"Found results for '{query_b}' but nothing for '{query_a}'."
        if not results_b:
            return f"Found results for '{query_a}' but nothing for '{query_b}'."
        return (
            f"For '{query_a}', I recommend {results_a[0]['food_name']}. "
            f"For '{query_b}', {results_b[0]['food_name']} would be a great choice."
        )
