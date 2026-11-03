# VidEarn Backend

FastAPI API with SQLAlchemy 2, Alembic, PostgreSQL, Redis/Celery, Firebase ID-token verification, rotated JWT refresh sessions, and a base admin RBAC boundary.

Run locally:

```bash
cp ../.env.example ../.env
docker compose up -d postgres redis
pip install -e .
alembic upgrade head
python scripts/seed.py
uvicorn app.main:app --reload
```

OpenAPI is available at `http://localhost:8000/docs`.
