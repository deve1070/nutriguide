from typing import List, Optional

from pydantic import BaseModel, Field
from datetime import datetime

# ── Request schemas ───────────────────────────────────


class ChatRequest(BaseModel):
    query: str = Field(
        ..., min_length=2, max_length=500, description="Natural language food query"
    )
    max_calories: Optional[int] = Field(
        None, gt=0, description="Max calories per serving filter"
    )
    cuisine_preference: Optional[str] = Field(
        None, description="Cuisine type preference for this query"
    )
    n_results: int = Field(5, ge=1, le=10, description="Number of results to retrieve")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": "I want something light and healthy for dinner",
                    "max_calories": 400,
                    "cuisine_preference": "Mediterranean",
                    "n_results": 5,
                }
            ]
        }
    }


class CompareRequest(BaseModel):
    query_a: str = Field(..., min_length=2, max_length=300)
    query_b: str = Field(..., min_length=2, max_length=300)


class ChatHistoryItem(BaseModel):
    id: int
    role: str
    content: str
    source: List[dict] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatHistoryResponse(BaseModel):
    messages: List[ChatHistoryItem]
    total: int


# ── Response schemas ──────────────────────────────────


class FoodResult(BaseModel):
    food_id: str
    food_name: str
    food_description: str
    cuisine_type: str
    food_calories_per_serving: int
    food_ingredients: str
    food_health_benefits: str
    cooking_method: str
    taste_profile: str
    similarity_score: float


class FiltersApplied(BaseModel):
    cuisine: Optional[str]
    max_calories: Optional[int]
    conditions: List[str]


class ChatResponse(BaseModel):
    response: str
    sources: List[FoodResult]
    total_results_found: int
    filters_applied: FiltersApplied
    condition_notes: List[str] = Field(
        default=[],
        description="Clinical notes explaining how conditions affected recommendations",
    )
    personalized: bool = Field(
        description="True if the user had a health profile applied"
    )


class CompareQueryResult(BaseModel):
    query: str
    results: List[FoodResult]


class CompareResponse(BaseModel):
    comparison: str
    query_a: CompareQueryResult
    query_b: CompareQueryResult
