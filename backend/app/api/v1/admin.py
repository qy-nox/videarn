from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID
import pyotp
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import desc, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import current_admin, require_permission
from app.core.config import get_settings
from app.core.security import create_token, verify_password
from app.db.session import get_db
from app.models import (
    AdminUser, AdConfig, AppSetting, AuditLog, CoinLedger, Device, FraudFlag,
    Hashtag, PayoutBudget, Report, Role, User, UserStatus, Video, VideoStatus,
    VideoStats, WithdrawalRequest, WithdrawalStatus,
)

router = APIRouter(prefix="/admin", tags=["admin"])

class AdminLogin(BaseModel):
    email: str
    password: str
    totp_code: str | None = None

class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class StatusUpdate(BaseModel):
    status: str
    reason: str = Field(min_length=1, max_length=500)

class EconomyUpdate(BaseModel):
    values: dict

class RevenueUpdate(BaseModel):
    estimated_revenue_usd: Decimal = Field(ge=0)

class SettingUpdate(BaseModel):
    value: dict

@router.post("/auth/login", response_model=AdminLoginResponse)
async def admin_login(payload: AdminLogin, db: AsyncSession = Depends(get_db)):
    admin = await db.scalar(select(AdminUser).where(AdminUser.email == payload.email.lower(), AdminUser.is_active.is_(True)))
    if not admin or not verify_password(payload.password, admin.password_hash):
        raise HTTPException(401, "Invalid administrator credentials")
    if admin.totp_secret and (not payload.totp_code or not pyotp.TOTP(admin.totp_secret).verify(payload.totp_code)):
        raise HTTPException(401, "Valid TOTP code required")
    return AdminLoginResponse(access_token=create_token(str(admin.id), "admin", timedelta(minutes=30)))

@router.get("/health")
async def health(_: AdminUser = Depends(current_admin)): return {"ok": True}

@router.get("/dashboard")
async def dashboard(_: AdminUser = Depends(require_permission("dashboard.read")), db: AsyncSession = Depends(get_db)):
    users = await db.scalar(select(func.count(User.id)))
    new_users = await db.scalar(select(func.count(User.id)).where(User.created_at >= datetime.now(timezone.utc) - timedelta(days=30)))
    videos = await db.scalar(select(func.count(Video.id)))
    views = await db.scalar(select(func.coalesce(func.sum(VideoStats.views), 0)))
    pending_withdrawals = await db.scalar(select(func.count(WithdrawalRequest.id)).where(WithdrawalRequest.status == WithdrawalStatus.pending))
    reports = await db.scalar(select(func.count(Report.id)).where(Report.status == "open"))
    fraud = await db.scalar(select(func.count(FraudFlag.id)).where(FraudFlag.resolved_at.is_(None)))
    budget = await db.scalar(select(PayoutBudget).order_by(PayoutBudget.budget_date.desc()))
    return {"users": users or 0, "new_users_30d": new_users or 0, "videos": videos or 0, "views": views or 0,
            "pending_withdrawals": pending_withdrawals or 0, "open_reports": reports or 0, "fraud_alerts": fraud or 0,
            "payout_budget": {"estimated_revenue_usd": float(budget.estimated_revenue_usd) if budget else 0,
                              "issued_coins": budget.issued_coins if budget else 0, "paused": budget.paused if budget else False}}

@router.get("/users")
async def users(q: str | None = None, status: str | None = None, limit: int = Query(50, ge=1, le=200),
                offset: int = Query(0, ge=0), _: AdminUser = Depends(require_permission("users.read")),
                db: AsyncSession = Depends(get_db)):
    query = select(User).order_by(desc(User.created_at)).offset(offset).limit(limit)
    if q: query = query.where(or_(User.username.ilike(f"%{q}%"), User.email.ilike(f"%{q}%"), User.phone.ilike(f"%{q}%")))
    if status: query = query.where(User.status == status)
    rows = (await db.execute(query)).scalars().all()
    return [{"id": str(x.id), "username": x.username, "email": x.email, "phone": x.phone, "status": x.status.value,
             "fraud_score": x.fraud_score, "phone_verified": x.phone_verified, "created_at": x.created_at.isoformat()} for x in rows]

@router.get("/users/{user_id}")
async def user_detail(user_id: UUID, _: AdminUser = Depends(require_permission("users.read")), db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user: raise HTTPException(404, "User not found")
    devices = (await db.execute(select(Device).where(Device.user_id == user_id))).scalars().all()
    flags = (await db.execute(select(FraudFlag).where(FraudFlag.user_id == user_id).order_by(desc(FraudFlag.created_at)))).scalars().all()
    return {"id": str(user.id), "username": user.username, "email": user.email, "status": user.status.value,
            "fraud_score": user.fraud_score, "devices": [{"id": str(x.id), "fingerprint": x.fingerprint, "integrity_ok": x.integrity_ok} for x in devices],
            "fraud_flags": [{"reason": x.reason, "score": x.score, "resolved_at": x.resolved_at} for x in flags]}

@router.patch("/users/{user_id}/status")
async def user_status(user_id: UUID, payload: StatusUpdate, request: Request,
                      admin: AdminUser = Depends(require_permission("users.moderate")), db: AsyncSession = Depends(get_db)):
    try: new_status = UserStatus(payload.status)
    except ValueError as exc: raise HTTPException(422, "Invalid user status") from exc
    user = await db.get(User, user_id)
    if not user: raise HTTPException(404, "User not found")
    before = {"status": user.status.value}; user.status = new_status
    db.add(AuditLog(admin_id=admin.id, action="user_status", entity_type="user", entity_id=str(user.id),
                    before=before, after={"status": payload.status, "reason": payload.reason}, ip=request.client.host if request.client else None))
    await db.commit()
    return {"id": str(user.id), "status": user.status.value}

@router.get("/videos")
async def videos(status: str | None = None, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0),
                 _: AdminUser = Depends(require_permission("videos.read")), db: AsyncSession = Depends(get_db)):
    query = select(Video, VideoStats).outerjoin(VideoStats, VideoStats.video_id == Video.id).order_by(desc(Video.created_at)).offset(offset).limit(limit)
    if status: query = query.where(Video.status == status)
    rows = (await db.execute(query)).all()
    return [{"id": str(video.id), "creator_id": str(video.creator_id), "caption": video.caption, "status": video.status.value,
             "thumbnail_url": video.thumbnail_url, "stats": {"views": stats.views if stats else 0, "likes": stats.likes if stats else 0}} for video, stats in rows]

@router.patch("/videos/{video_id}/status")
async def video_status(video_id: UUID, payload: StatusUpdate, request: Request,
                       admin: AdminUser = Depends(require_permission("videos.moderate")), db: AsyncSession = Depends(get_db)):
    try: new_status = VideoStatus(payload.status)
    except ValueError as exc: raise HTTPException(422, "Invalid video status") from exc
    video = await db.get(Video, video_id)
    if not video: raise HTTPException(404, "Video not found")
    before = {"status": video.status.value}; video.status = new_status
    db.add(AuditLog(admin_id=admin.id, action="video_status", entity_type="video", entity_id=str(video.id),
                    before=before, after={"status": payload.status, "reason": payload.reason}, ip=request.client.host if request.client else None))
    await db.commit()
    return {"id": str(video.id), "status": video.status.value}

@router.get("/reports")
async def reports(status: str | None = "open", _: AdminUser = Depends(require_permission("reports.read")), db: AsyncSession = Depends(get_db)):
    query = select(Report).order_by(desc(Report.created_at))
    if status: query = query.where(Report.status == status)
    rows = (await db.execute(query.limit(200))).scalars().all()
    return [{"id": str(x.id), "target_type": x.target_type, "target_id": str(x.target_id), "reason": x.reason, "status": x.status} for x in rows]

@router.get("/withdrawals")
async def withdrawals(status: str | None = "pending", _: AdminUser = Depends(require_permission("finance.read")), db: AsyncSession = Depends(get_db)):
    query = select(WithdrawalRequest).order_by(desc(WithdrawalRequest.created_at))
    if status: query = query.where(WithdrawalRequest.status == status)
    rows = (await db.execute(query.limit(200))).scalars().all()
    return [{"id": str(x.id), "user_id": str(x.user_id), "amount_coins": x.amount_coins, "status": x.status.value,
             "rejection_reason": x.rejection_reason, "created_at": x.created_at.isoformat()} for x in rows]

@router.patch("/withdrawals/{withdrawal_id}")
async def withdrawal_status(withdrawal_id: UUID, payload: StatusUpdate, request: Request,
                            admin: AdminUser = Depends(require_permission("finance.write")), db: AsyncSession = Depends(get_db)):
    try: new_status = WithdrawalStatus(payload.status)
    except ValueError as exc: raise HTTPException(422, "Invalid withdrawal status") from exc
    row = await db.get(WithdrawalRequest, withdrawal_id)
    if not row: raise HTTPException(404, "Withdrawal not found")
    if row.status == WithdrawalStatus.paid: raise HTTPException(409, "Paid withdrawal cannot change")
    before = {"status": row.status.value}; row.status = new_status
    row.rejection_reason = payload.reason if new_status == WithdrawalStatus.rejected else None
    db.add(AuditLog(admin_id=admin.id, action="withdrawal_status", entity_type="withdrawal", entity_id=str(row.id),
                    before=before, after={"status": payload.status, "reason": payload.reason}, ip=request.client.host if request.client else None))
    await db.commit()
    return {"id": str(row.id), "status": row.status.value}

@router.get("/economy")
async def economy(_: AdminUser = Depends(require_permission("economy.read")), db: AsyncSession = Depends(get_db)):
    row = await db.scalar(select(AppSetting).where(AppSetting.key == "economy"))
    return row.value if row else {}

@router.put("/economy")
async def update_economy(payload: EconomyUpdate, request: Request, admin: AdminUser = Depends(require_permission("economy.write")), db: AsyncSession = Depends(get_db)):
    row = await db.scalar(select(AppSetting).where(AppSetting.key == "economy"))
    before = row.value if row else {}
    if row: row.value = payload.values; row.version += 1
    else: db.add(AppSetting(key="economy", value=payload.values, version=1))
    db.add(AuditLog(admin_id=admin.id, action="economy_update", entity_type="app_setting", entity_id="economy",
                    before=before, after=payload.values, ip=request.client.host if request.client else None))
    await db.commit()
    return payload.values

@router.get("/ads")
async def ads(_: AdminUser = Depends(require_permission("ads.read")), db: AsyncSession = Depends(get_db)):
    config = await db.get(AdConfig, 1)
    return {"in_feed_frequency": config.in_feed_frequency if config else 5, "daily_reward_cap": config.daily_reward_cap if config else 10,
            "cooldown_seconds": config.cooldown_seconds if config else 60}

@router.put("/ads")
async def update_ads(payload: dict, admin: AdminUser = Depends(require_permission("ads.write")), db: AsyncSession = Depends(get_db)):
    config = await db.get(AdConfig, 1)
    if not config: config = AdConfig(id=1); db.add(config)
    for key in ("in_feed_frequency", "daily_reward_cap", "cooldown_seconds"):
        if key in payload: setattr(config, key, int(payload[key]))
    await db.commit()
    return {"ok": True}

@router.put("/payout-budget")
async def update_budget(payload: RevenueUpdate, _: AdminUser = Depends(require_permission("finance.write")), db: AsyncSession = Depends(get_db)):
    from app.services.economy import today_budget
    budget = await today_budget(db, lock=True)
    budget.estimated_revenue_usd = payload.estimated_revenue_usd
    budget.paused = False
    await db.commit()
    return {"estimated_revenue_usd": float(budget.estimated_revenue_usd), "issued_coins": budget.issued_coins}

@router.get("/fraud")
async def fraud(_: AdminUser = Depends(require_permission("fraud.read")), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(FraudFlag).where(FraudFlag.resolved_at.is_(None)).order_by(desc(FraudFlag.score)).limit(200))).scalars().all()
    return [{"id": str(x.id), "user_id": str(x.user_id), "reason": x.reason, "score": x.score} for x in rows]

@router.get("/audit-logs")
async def audit_logs(_: AdminUser = Depends(require_permission("audit.read")), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(AuditLog).order_by(desc(AuditLog.created_at)).limit(200))).scalars().all()
    return [{"id": str(x.id), "admin_id": str(x.admin_id) if x.admin_id else None, "action": x.action,
             "entity_type": x.entity_type, "entity_id": x.entity_id, "created_at": x.created_at.isoformat()} for x in rows]

@router.get("/settings")
async def settings(_: AdminUser = Depends(require_permission("settings.read")), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(AppSetting).order_by(AppSetting.key))).scalars().all()
    return [{"key": x.key, "value": x.value, "version": x.version} for x in rows]

@router.put("/settings/{key}")
async def update_setting(key: str, payload: SettingUpdate, admin: AdminUser = Depends(require_permission("settings.write")), db: AsyncSession = Depends(get_db)):
    row = await db.get(AppSetting, key)
    if row: row.value = payload.value; row.version += 1
    else: db.add(AppSetting(key=key, value=payload.value, version=1))
    await db.commit()
    return {"key": key, "value": payload.value}

@router.get("/roles")
async def roles(_: AdminUser = Depends(require_permission("admins.read")), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Role).order_by(Role.name))).scalars().all()
    return [{"id": x.id, "name": x.name, "permissions": x.permissions} for x in rows]

@router.get("/admin-users")
async def admin_users(_: AdminUser = Depends(require_permission("admins.read")), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(AdminUser, Role).join(Role, Role.id == AdminUser.role_id))).all()
    return [{"id": str(admin.id), "email": admin.email, "active": admin.is_active, "role": role.name} for admin, role in rows]

@router.get("/hashtags")
async def hashtags(_: AdminUser = Depends(require_permission("content.read")), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Hashtag).order_by(Hashtag.name))).scalars().all()
    return [{"id": x.id, "name": x.name} for x in rows]
