# ClipEarn Backend

FastAPI API with SQLAlchemy 2, Alembic, PostgreSQL, Redis/Celery, Firebase ID-token verification, rotated JWT refresh sessions, auditable rewards, and a permission-checked admin API.

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

## Phase 3

Wallet-changing requests use idempotency keys and write immutable coin ledger entries while
locking wallet rows. Rewarded ads are credited only from the verified AdMob SSV callback;
`transaction_id` is deduplicated. Daily caps, cooldowns, check-in streaks, referral
qualification, withdrawal age/phone rules, encrypted payout details, fraud scoring, and a
daily payout-budget pause are implemented.

After pulling Phase 3:

```bash
alembic upgrade head
python scripts/seed.py
```

## Phase 4

The admin API is available under `/api/v1/admin`, requires a short-lived admin JWT, and
checks role permissions for every protected route. The React console provides dashboard,
user/video moderation, reports, finance, ads, economy, fraud, content, settings, admin,
audit, notifications, and support navigation surfaces.

Run the console:

```bash
cd ../admin
npm install
VITE_API_URL=http://localhost:8000/api/v1 npm run dev
```
