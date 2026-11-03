# VidEarn Admin

React + Vite + TypeScript operations console. It uses the RBAC-protected `/api/v1/admin`
API and stores only the short-lived admin access token in browser local storage.

```bash
npm install
VITE_API_URL=http://localhost:8000/api/v1 npm run dev
```

Open `http://localhost:5173`. Default seeded credentials are configured by `ADMIN_EMAIL`
and `ADMIN_PASSWORD` in the backend `.env`.
