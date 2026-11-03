# ClipEarn

ClipEarn is a production-oriented short-video social and rewards platform for Bangladesh and international expansion. It combines vertical video discovery, creator publishing, verified rewarded advertising, an auditable coin ledger, redemption workflows, and a role-protected operations console.

## Current implementation

```bash
cp .env.example .env
sudo docker compose up -d postgres redis
```

The repository already contains the backend foundation, media pipeline, feed and engagement APIs, wallet/reward services, and admin console. These are being aligned to the ClipEarn specification incrementally rather than discarded.

API docs: http://localhost:8000/docs

## Development roadmap

1. Core foundation and authentication
2. Media pipeline, feed, discovery, and search
3. Social engagement, notifications, and moderation
4. Wallet, verified rewards, missions, and referrals
5. Redemptions, creator monetization, and finance
6. Complete admin analytics, support, CMS, and settings
7. Security, performance, deployment, and documentation

See `backend/README.md` and `admin/README.md` for run instructions.
