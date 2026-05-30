from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import models so SQLAlchemy registers them before create_all
import backend.models  # noqa: F401
from backend.config import get_settings
from backend.database import Base, engine

# Routers
from backend.routers import auth, profile

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"🚀 Starting {settings.app_name} [{settings.app_env}]")

    import time

    max_retries = 10
    for attempt in range(max_retries):
        try:
            Base.metadata.create_all(bind=engine)
            print("✅ Database tables ready")
            break
        except Exception:
            if attempt < max_retries - 1:
                print(
                    f"⏳ DB not ready (attempt {attempt + 1}/{max_retries}), retrying in 3s..."
                )
                time.sleep(3)
            else:
                raise

    yield

    print(f"🛑 Shutting down {settings.app_name}")


# ── App instance ──────────────────────────────────────
app = FastAPI(
    title="NutriGuide API",
    description=(
        "Clinical Nutrition Intelligence Platform — "
        "personalized food recommendations powered by RAG and Llama 3.1"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────
app.include_router(auth.router)
app.include_router(profile.router)
# Phase 3 — added next:
# app.include_router(recommendations.router)
# app.include_router(search.router)
# Phase 4 — added next:
# app.include_router(meal_plan.router)
# app.include_router(analytics.router)


# ── Health check ──────────────────────────────────────
@app.get("/", tags=["Health"], summary="API health check")
def root():
    return JSONResponse(
        {
            "status": "ok",
            "app": settings.app_name,
            "version": "1.0.0",
            "env": settings.app_env,
            "docs": "/docs",
        }
    )


@app.get("/health", tags=["Health"], summary="Detailed health check")
def health_check():
    return JSONResponse(
        {
            "status": "healthy",
            "database": "connected",
            "llm_provider": "groq",
            "model": settings.groq_model_id,
        }
    )
