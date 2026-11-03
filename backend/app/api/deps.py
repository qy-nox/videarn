from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models import User, AdminUser
from app.core.security import decode_token
bearer = HTTPBearer()
async def current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer), db: AsyncSession = Depends(get_db)) -> User:
    try: data = decode_token(credentials.credentials)
    except Exception as exc: raise HTTPException(status_code=401, detail={"code":"invalid_token","message":"Invalid access token"}) from exc
    if data.get("type") != "access": raise HTTPException(401, "Access token required")
    user = await db.scalar(select(User).where(User.id == data["sub"]))
    if not user or user.status.value != "active": raise HTTPException(401, "User is not active")
    return user
async def current_admin(credentials: HTTPAuthorizationCredentials = Depends(bearer), db: AsyncSession = Depends(get_db)) -> AdminUser:
    try: data = decode_token(credentials.credentials)
    except Exception as exc: raise HTTPException(401, "Invalid admin token") from exc
    if data.get("type") != "admin": raise HTTPException(403, "Admin token required")
    admin = await db.scalar(select(AdminUser).where(AdminUser.id == data["sub"], AdminUser.is_active.is_(True)))
    if not admin: raise HTTPException(403, "Admin access denied")
    return admin
