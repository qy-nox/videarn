from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import current_user
from app.core.config import get_settings
from app.core.security import create_token, decode_token
from app.db.session import get_db
from app.models import AuthSession, User
from app.schemas.auth import FirebaseLoginRequest, RefreshRequest, TokenResponse, UserResponse
from app.services.firebase import verify_firebase_token
router = APIRouter(prefix="/auth", tags=["auth"])
def issue_tokens(user_id: str) -> TokenResponse:
    s=get_settings(); access=create_token(user_id,"access",timedelta(minutes=s.jwt_access_minutes)); refresh=create_token(user_id,"refresh",timedelta(days=s.jwt_refresh_days)); return TokenResponse(access_token=access, refresh_token=refresh)
@router.post("/firebase-login", response_model=TokenResponse)
async def firebase_login(payload: FirebaseLoginRequest, db: AsyncSession=Depends(get_db)):
    try: claims=verify_firebase_token(payload.id_token)
    except Exception as exc: raise HTTPException(401, "Firebase token verification failed") from exc
    user=await db.scalar(select(User).where(User.firebase_uid==claims["uid"]))
    if not user:
        user=User(firebase_uid=claims["uid"],phone=claims.get("phone_number"),email=claims.get("email"),phone_verified=bool(claims.get("phone_number"))); db.add(user); await db.flush()
    tokens=issue_tokens(str(user.id)); db.add(AuthSession(user_id=user.id,refresh_token_hash=tokens.refresh_token,expires_at=datetime.now(timezone.utc)+timedelta(days=get_settings().jwt_refresh_days))); await db.commit(); return tokens
@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, db: AsyncSession=Depends(get_db)):
    try: data=decode_token(payload.refresh_token)
    except Exception as exc: raise HTTPException(401,"Invalid refresh token") from exc
    if data.get("type")!="refresh": raise HTTPException(401,"Refresh token required")
    session=await db.scalar(select(AuthSession).where(AuthSession.refresh_token_hash==payload.refresh_token,AuthSession.revoked_at.is_(None)))
    if not session: raise HTTPException(401,"Refresh session revoked")
    session.revoked_at=datetime.now(timezone.utc); tokens=issue_tokens(str(session.user_id)); db.add(AuthSession(user_id=session.user_id,refresh_token_hash=tokens.refresh_token,expires_at=datetime.now(timezone.utc)+timedelta(days=get_settings().jwt_refresh_days))); await db.commit(); return tokens
@router.post("/logout")
async def logout(user: User=Depends(current_user), db: AsyncSession=Depends(get_db)):
    await db.execute(AuthSession.__table__.update().where(AuthSession.user_id==user.id,AuthSession.revoked_at.is_(None)).values(revoked_at=datetime.now(timezone.utc))); await db.commit(); return {"ok":True}
@router.delete("/me")
async def delete_me(user: User=Depends(current_user), db: AsyncSession=Depends(get_db)):
    user.status="deleted"; await db.commit(); return {"ok":True}
@router.get("/me", response_model=UserResponse)
async def me(user: User=Depends(current_user)): return user
