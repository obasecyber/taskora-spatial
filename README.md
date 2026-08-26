# Taskora Spatial

M0 platform foundation for a normalized, provenance-aware spatial data platform.

## Local setup

Requirements: Python 3.12, Docker Desktop with Compose, and Git.

```powershell
Copy-Item .env.example .env
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
docker compose up -d db
alembic upgrade head
pytest
uvicorn backend.app.main:app --reload
```

The API health check is available at http://localhost:8000/api/v1/health. To run the API and database together, use `docker compose up --build`.

To validate the migration lifecycle against a clean database:

```powershell
docker compose down -v
docker compose up --build
docker compose exec api alembic downgrade base
docker compose exec api alembic upgrade head
```

Compose waits for PostgreSQL readiness before starting the API, and the API health check verifies database connectivity. CI uses separate non-production database credentials, waits explicitly with `pg_isready`, and repeats the clean migration cycle.

The database image provides PostgreSQL 16, PostGIS, and pgvector. Database credentials are development-only defaults; set them through `.env` or the Compose environment and never commit `.env`.

## Architecture notes

Country-specific adapters live under `ingestion/` and emit source records into the normalized model. Every ingestible entity preserves `data_source_id`, `source_record_id`, ingestion-run context, source timestamps, and raw payloads. Source accessibility does not imply commercial approval; approval is explicit on `data_sources`.

The opportunity engine, forecasting, CRM, lead generation, and dashboard are intentionally outside M0.