from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.core.vector_store import VectorStore, get_vector_store
from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.health_profile import HealthProfile
from backend.models.user import User
from backend.schemas.recommendation import (
    ChatRequest,
    ChatResponse,
    CompareQueryResult,
    CompareRequest,
    CompareResponse,
)
from backend.services.llm_client import LLMClient, get_llm_client
from backend.services.rag_engine import RAGEngine

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


def get_rag_engine(
    vector_store: VectorStore = Depends(get_vector_store),
    llm_client: LLMClient = Depends(get_llm_client),
) -> RAGEngine:
    return RAGEngine(vector_store=vector_store, llm_client=llm_client)


def _get_user_profile(user: User, db: Session) -> HealthProfile | None:
    return db.query(HealthProfile).filter(HealthProfile.user_id == user.id).first()


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Get personalized food recommendations via RAG",
    description=(
        "Send a natural language food query. The system retrieves semantically "
        "similar foods from the vector database, then uses Llama 3.1 to generate "
        "a personalized response based on your health profile."
    ),
)
def chat(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    engine: RAGEngine = Depends(get_rag_engine),
):
    profile = _get_user_profile(current_user, db)

    # Pull health context from profile if available
    conditions = profile.conditions if profile else []
    dietary_restrictions = profile.dietary_restrictions if profile else []
    allergies = profile.allergies if profile else []
    preferred_cuisines = profile.preferred_cuisines if profile else []
    calorie_target = profile.daily_calorie_target if profile else None

    # Per-request override takes priority over profile calorie target
    max_calories = payload.max_calories or calorie_target
    cuisine = payload.cuisine_preference or (
        preferred_cuisines[0] if preferred_cuisines else None
    )

    result = engine.chat(
        query=payload.query,
        conditions=conditions,
        dietary_restrictions=dietary_restrictions,
        allergies=allergies,
        preferred_cuisines=[cuisine] if cuisine else [],
        max_calories=max_calories,
        n_results=payload.n_results,
    )

    return ChatResponse(
        response=result["response"],
        sources=result["sources"],
        total_results_found=result["total_results_found"],
        filters_applied=result["filters_applied"],
        personalized=bool(conditions or dietary_restrictions or allergies),
    )


@router.post(
    "/compare",
    response_model=CompareResponse,
    summary="Compare two food queries side-by-side with AI analysis",
)
def compare(
    payload: CompareRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    engine: RAGEngine = Depends(get_rag_engine),
):
    profile = _get_user_profile(current_user, db)
    conditions = profile.conditions if profile else []

    result = engine.compare(
        query_a=payload.query_a,
        query_b=payload.query_b,
        conditions=conditions,
    )

    return CompareResponse(
        comparison=result["comparison"],
        query_a=CompareQueryResult(
            query=payload.query_a,
            results=result["query_a"]["results"],
        ),
        query_b=CompareQueryResult(
            query=payload.query_b,
            results=result["query_b"]["results"],
        ),
    )


@router.get(
    "/health-check",
    summary="Check if LLM and vector store are reachable",
    tags=["Health"],
)
def recommendations_health(
    vector_store: VectorStore = Depends(get_vector_store),
    llm_client: LLMClient = Depends(get_llm_client),
):
    return {
        "vector_store_count": vector_store.get_collection().count(),
        "llm_available": llm_client.is_available(),
    }
