from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from backend.core.vector_store import VectorStore, get_vector_store
from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.chat_message import ChatMessage
from backend.models.health_profile import HealthProfile
from backend.models.user import User
from backend.schemas.recommendation import (
    ChatHistoryItem,
    ChatHistoryResponse,
    ChatRequest,
    ChatResponse,
    CompareQueryResult,
    CompareRequest,
    CompareResponse,
)
from backend.services.condition_filter import ConditionFilter, get_condition_filter
from backend.services.llm_client import LLMClient, get_llm_client
from backend.services.rag_engine import RAGEngine

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

# How many past messages to pass to the LLM for memory
MEMORY_WINDOW = 10  # last 10 exchanges = 20 messages


def get_rag_engine(
    vector_store: VectorStore = Depends(get_vector_store),
    llm_client: LLMClient = Depends(get_llm_client),
    condition_filter: ConditionFilter = Depends(get_condition_filter),
) -> RAGEngine:
    return RAGEngine(
        vector_store=vector_store,
        llm_client=llm_client,
        condition_filter=condition_filter,
    )


def _get_user_profile(user: User, db: Session) -> HealthProfile | None:
    return db.query(HealthProfile).filter(HealthProfile.user_id == user.id).first()


def _load_conversation_history(
    user_id: int, db: Session, limit: int = MEMORY_WINDOW * 2
) -> list[dict]:
    """
    Load recent messages and format them for the LLM.
    Returns [{"role": "user"|"assistant", "content": "..."}]
    """
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == user_id)
        .order_by(desc(ChatMessage.created_at))
        .limit(limit)
        .all()
    )
    # Reverse so oldest is first (chronological order for LLM)
    messages = list(reversed(messages))
    return [{"role": m.role, "content": m.content} for m in messages]


def _save_messages(
    user_id: int,
    user_content: str,
    assistant_content: str,
    sources: list,
    db: Session,
):
    """Save the user message and assistant response to DB"""
    db.add(
        ChatMessage(
            user_id=user_id,
            role="user",
            content=user_content,
            sources=[],
        )
    )
    db.add(
        ChatMessage(
            user_id=user_id,
            role="assistant",
            content=assistant_content,
            sources=sources,
        )
    )
    db.commit()


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Get personalized food recommendations via RAG",
    description=(
        "Send a natural language food query. The system retrieves semantically "
        "similar foods from the vector database, then uses Llama 3.1 to generate "
        "a personalized response based on your health profile and conversation history."
    ),
)
def chat(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    engine: RAGEngine = Depends(get_rag_engine),
):
    profile = _get_user_profile(current_user, db)

    conditions = profile.conditions if profile else []
    dietary_restrictions = profile.dietary_restrictions if profile else []
    allergies = profile.allergies if profile else []
    preferred_cuisines = profile.preferred_cuisines if profile else []
    calorie_target = profile.daily_calorie_target if profile else None

    max_calories = payload.max_calories or calorie_target
    cuisine = payload.cuisine_preference or (
        preferred_cuisines[0] if preferred_cuisines else None
    )

    # Load conversation history for memory
    history = _load_conversation_history(current_user.id, db)

    result = engine.chat(
        query=payload.query,
        conditions=conditions,
        dietary_restrictions=dietary_restrictions,
        allergies=allergies,
        preferred_cuisines=[cuisine] if cuisine else [],
        max_calories=max_calories,
        n_results=payload.n_results,
        conversation_history=history,
    )

    # Persist this exchange to DB
    _save_messages(
        user_id=current_user.id,
        user_content=payload.query,
        assistant_content=result["response"],
        sources=result["sources"],
        db=db,
    )

    return ChatResponse(
        response=result["response"],
        sources=result["sources"],
        total_results_found=result["total_results_found"],
        filters_applied=result["filters_applied"],
        condition_notes=result.get("condition_notes", []),
        personalized=bool(conditions or dietary_restrictions or allergies),
    )


@router.get(
    "/history",
    response_model=ChatHistoryResponse,
    summary="Get conversation history for the current user",
)
def get_history(
    limit: int = Query(50, ge=1, le=200, description="Number of messages to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == current_user.id)
        .order_by(ChatMessage.created_at)
        .limit(limit)
        .all()
    )
    return ChatHistoryResponse(
        messages=[ChatHistoryItem.model_validate(m) for m in messages],
        total=len(messages),
    )


@router.delete(
    "/history",
    summary="Clear conversation history for the current user",
)
def clear_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    deleted = (
        db.query(ChatMessage).filter(ChatMessage.user_id == current_user.id).delete()
    )
    db.commit()
    return {"message": f"Cleared {deleted} messages"}


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
