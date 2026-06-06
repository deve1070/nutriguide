from typing import List

from pydantic import BaseModel


class SearchResponse(BaseModel):
    query: str
    results: List[dict]
    total: int
    filters: dict


class FoodDetailResponse(BaseModel):
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
