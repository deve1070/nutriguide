from typing import Optional

from fastapi import APIRouter, Depends, Query

from backend.core.vector_store import VectorStore, get_vector_store
from backend.dependencies import get_current_user
from backend.models.user import User
from backend.schemas.search import SearchResponse

router = APIRouter(prefix="/search", tags=["Food Search"])

AVAILABLE_CUISINES = [
    "Italian",
    "Thai",
    "Mexican",
    "Indian",
    "Japanese",
    "French",
    "Mediterranean",
    "American",
    "Ethiopian",
    "Chinese",
    "Greek",
    "Lebanese",
    "Health Food",
    "Dessert",
]


@router.get(
    "/foods",
    response_model=SearchResponse,
    summary="Search foods with optional cuisine and calorie filters",
)
def search_foods(
    q: str = Query(..., min_length=1, description="Search query"),
    cuisine: Optional[str] = Query(None, description="Filter by cuisine type"),
    max_calories: Optional[int] = Query(
        None, gt=0, description="Max calories per serving"
    ),
    n: int = Query(5, ge=1, le=20, description="Number of results"),
    current_user: User = Depends(get_current_user),
    vector_store: VectorStore = Depends(get_vector_store),
):
    results = vector_store.similarity_search(
        query=q,
        n_results=n,
        cuisine_filter=cuisine,
        max_calories=max_calories,
    )

    return SearchResponse(
        query=q,
        results=results,
        total=len(results),
        filters={"cuisine": cuisine, "max_calories": max_calories},
    )


@router.get(
    "/cuisines",
    summary="List all available cuisine types",
)
def list_cuisines(current_user: User = Depends(get_current_user)):
    return {"cuisines": AVAILABLE_CUISINES}
