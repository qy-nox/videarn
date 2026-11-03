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

## Phase 2

The video API accepts a validated upload request, returns an S3-compatible presigned PUT URL,
creates a processing record, and queues `transcode_video`. The worker requires `ffmpeg` and
produces 360p, 540p, and 720p HLS renditions plus a JPEG thumbnail. Configure S3/R2 values
in `.env`; the worker marks videos `pending_review` after transcoding.

Feed endpoints are cursor-paginated and exclude videos already viewed in the last day,
blocked creators, and non-published content:

- `GET /api/v1/feed/for-you`
- `GET /api/v1/feed/following`
- `POST /api/v1/videos/{id}/view`
- `POST/DELETE /api/v1/videos/{id}/like`
- `POST /api/v1/videos/{id}/comments`
- `POST/DELETE /api/v1/users/{id}/follow`
