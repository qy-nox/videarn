# VidEarn Backend

FastAPI API with SQLAlchemy 2, Alembic, PostgreSQL, Redis/Celery, Firebase ID-token verification, rotated JWT refresh sessions, and a base admin RBAC boundary.

Run locally:

```bash
cd ..
cp .env.example .env
sed -i 's|@postgres:5432|@localhost:5432|' .env
docker compose up -d postgres redis
cd backend
cp ../.env .env
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
alembic upgrade head
python scripts/seed.py
uvicorn app.main:app --reload
```

OpenAPI is available at `http://localhost:8000/docs`.
