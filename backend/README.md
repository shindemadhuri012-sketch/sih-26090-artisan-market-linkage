# SIH 26090: Backend Application Layer

FastAPI async REST API service supporting intelligent artisan-buyer linkage, craft provenance verification, multi-stage explainable matching, and cost-plus-margin fair pricing.

## Architecture

```
backend/
├── app/
│   ├── api/          # Route handlers & endpoints (v1)
│   ├── core/         # Settings, database session, telemetry & security
│   ├── models/       # Declarative SQLAlchemy 2.0 ORM models (23 entities)
│   ├── schemas/      # Pydantic v2 DTOs (Request & Response validation)
│   ├── services/     # Pure business logic domain services
│   └── main.py       # FastAPI application factory
├── alembic/          # Database migrations
└── requirements.txt  # Dependencies
```

## Running the API
```bash
uvicorn app.main:app --reload --port 8000
```
API Documentation: `http://localhost:8000/docs`
