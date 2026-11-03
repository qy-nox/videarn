# VidEarn

Production-oriented short-video social app monorepo. Phase 1 provides the deployable backend foundation, PostgreSQL schema, migrations, seed data, Firebase-to-JWT authentication, and admin RBAC boundary.

## Phase 1

```bash
cp .env.example .env
docker compose up --build
docker compose exec api alembic upgrade head
docker compose exec api python scripts/seed.py
```

API docs: http://localhost:8000/docs

See `backend/README.md` for local backend commands. The `mobile/` and `admin/` directories are reserved for later phases.
