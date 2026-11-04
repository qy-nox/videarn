from fastapi import FastAPI
from app.api.v1.auth import router as auth_router
from app.api.v1.admin import router as admin_router
from app.api.v1.videos import router as videos_router
from app.api.v1.wallet import router as wallet_router
app=FastAPI(title="ClipEarn API", version="1.0.0")
app.include_router(auth_router,prefix="/api/v1"); app.include_router(admin_router,prefix="/api/v1"); app.include_router(videos_router,prefix="/api/v1"); app.include_router(wallet_router,prefix="/api/v1")
@app.get("/health")
async def health(): return {"status":"ok"}
