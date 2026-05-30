# 🥗 NutriGuide — Clinical Nutrition Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react)](https://react.dev)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-vector_search-orange)](https://www.trychroma.com)
[![IBM watsonx](https://img.shields.io/badge/IBM-Granite_LLM-1F70C1?logo=ibm)](https://www.ibm.com/watsonx)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Deploy on Render](https://img.shields.io/badge/Deployed-Render-46E3B7?logo=render)](https://render.com)

> **Personalized food recommendations for people living with chronic conditions** — powered by RAG (Retrieval-Augmented Generation), IBM Granite, and ChromaDB vector search.

---

## The Problem

Over **537 million adults** live with diabetes globally. Millions more manage hypertension, kidney disease, or PCOS daily. Yet most leave clinical appointments without practical, personalized food guidance. Generic nutrition apps treat everyone the same. Dietitians are expensive and scarce.

**NutriGuide bridges that gap** — it understands a user's health profile and delivers food recommendations that are safe, relevant, and explained in plain language.

---

## Key Features

| Feature                          | Description                                                                       |
| -------------------------------- | --------------------------------------------------------------------------------- |
| 🧠 **RAG-powered chat**          | Natural language queries against a vector food database                           |
| 🏥 **Condition-aware filtering** | Recommendations re-ranked by clinical safety rules (diabetes, hypertension, etc.) |
| 📅 **7-day meal planner**        | Full week of meals generated around your health goals                             |
| 🔍 **Advanced food search**      | Filter by cuisine, calories, ingredients, and health score                        |
| 📊 **Nutrition analytics**       | Track trends and adherence over time                                              |
| 👨‍⚕️ **Clinician dashboard**       | Role-based access for dietitians to review AI suggestions                         |
| 🔒 **JWT auth**                  | Secure user accounts with role-based permissions                                  |
| 📖 **OpenAPI docs**              | Interactive API documentation at `/docs`                                          |

---

## Architecture

```
┌─────────────┐    ┌─────────────┐    ┌──────────────┐
│  React SPA  │    │  Mobile PWA │    │  3rd-party   │
│  (Vite)     │    │             │    │  EHR/clinics │
└──────┬──────┘    └──────┬──────┘    └──────┬───────┘
       │                  │                  │
       └──────────────────▼──────────────────┘
                  ┌───────────────┐
                  │  FastAPI      │
                  │  (Python 3.11)│
                  │  JWT · CORS   │
                  └───────┬───────┘
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
   ┌─────────────┐ ┌───────────┐ ┌──────────────┐
   │  RAG Engine │ │ Meal Plan │ │  Analytics   │
   │  + Condition│ │ Generator │ │  Service     │
   │  Filter     │ └─────┬─────┘ └──────┬───────┘
   └──────┬──────┘       │              │
          └──────────────▼──────────────┘
     ┌──────────┐  ┌──────────┐  ┌──────────┐
     │ ChromaDB │  │PostgreSQL│  │   IBM    │
     │ (vectors)│  │(profiles)│  │ Granite  │
     └──────────┘  └──────────┘  └──────────┘
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Groq API key

### 1. Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/nutriguide.git
cd nutriguide

# Backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your database URL and IBM API key
```

### 3. Run locally

```bash
# Terminal 1 — API
uvicorn backend.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend && npm run dev
```

API docs: **http://localhost:8000/docs**
Frontend: **http://localhost:5173**

---

## API Endpoints

| Method | Endpoint                      | Description               |
| ------ | ----------------------------- | ------------------------- |
| `POST` | `/auth/register`              | Create account            |
| `POST` | `/auth/login`                 | Get JWT token             |
| `GET`  | `/profile/me`                 | Get my profile            |
| `PUT`  | `/profile/health`             | Update conditions & goals |
| `POST` | `/recommendations/chat`       | RAG food chat             |
| `GET`  | `/recommendations/history`    | Past recommendations      |
| `POST` | `/meal-plan/generate`         | Generate 7-day plan       |
| `GET`  | `/search/foods`               | Advanced food search      |
| `GET`  | `/analytics/nutrition-trends` | My nutrition trends       |

Full interactive docs at `/docs` (Swagger UI) and `/redoc`.

---

## Supported Health Conditions

- **Type 2 Diabetes** — low glycemic index prioritization, sugar filtering
- **Hypertension** — low sodium recommendations
- **Chronic Kidney Disease** — phosphorus and potassium limits
- **PCOS** — anti-inflammatory, hormone-balancing foods
- **Celiac / Gluten intolerance** — gluten-free filtering
- **Lactose intolerance** — dairy filtering

---

## Deployment

This project is deployed on **Render** using a `render.yaml` blueprint.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for full instructions.

---

## Project Structure

```
nutriguide/
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Settings via pydantic-settings
│   ├── dependencies.py      # Auth + DB session injection
│   ├── routers/             # Route handlers
│   ├── services/            # Business logic
│   ├── models/              # SQLAlchemy ORM models
│   ├── schemas/             # Pydantic request/response schemas
│   └── core/                # Vector store, embeddings, clinical rules
├── frontend/
│   └── src/
│       ├── pages/           # Chat, MealPlan, Dashboard, Onboarding
│       └── components/      # Reusable UI components
├── tests/                   # pytest test suite
├── .github/workflows/       # CI/CD pipelines
├── render.yaml              # Render deployment blueprint
└── docker-compose.yml       # Local dev with Postgres
```

---

## Tech Stack

**Backend:** Python 3.11 · FastAPI · SQLAlchemy · Alembic · ChromaDB · Sentence Transformers · IBM Granite LLM

**Frontend:** React 18 · Vite · Tailwind CSS · React Query

**Database:** PostgreSQL · ChromaDB (vector)

**DevOps:** Docker · GitHub Actions · Render

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first.

---

## License

[MIT](LICENSE)

---

_Built as a portfolio project demonstrating production-ready RAG architecture for clinical nutrition use cases._
