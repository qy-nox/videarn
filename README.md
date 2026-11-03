# VidEarn

Production-oriented short-video social app monorepo. Phase 1 provides the deployable backend foundation, PostgreSQL schema, migrations, seed data, Firebase-to-JWT authentication, and admin RBAC boundary.

## Phase 1

```bash
cp .env.example .env
docker compose up --build
```

API docs: http://localhost:8000/docs

For local API execution, copy the root environment file into `backend/.env`, then run Alembic and the seed script from `backend/`. See `backend/README.md` for exact commands. The `mobile/` and `admin/` directories are reserved for later phases.
