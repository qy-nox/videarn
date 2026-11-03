import base64
import hashlib
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from cryptography.fernet import Fernet
from app.api.deps import current_user
from app.core.config import get_settings
from app.db.session import get_db
from app.models import AdConfig, CoinLedger, DailyCheckin, Referral, RewardedAdEvent, User, WithdrawalRequest, WithdrawalStatus, PayoutMethod
from app.schemas.wallet import CheckinResponse, ReferralApplyRequest, WithdrawalRequestModel
from app.services.economy import economy_settings, get_or_create_wallet, issue_coins, debit_coins
from app.services.fraud import assess_user
from app.services.referrals import qualify_if_ready
from app.services.ssv import verify_ssv_signature

router = APIRouter(tags=["wallet", "ads", "referrals"])

def encrypt_details(details: dict) -> str:
    key = base64.urlsafe_b64encode(hashlib.sha256(get_settings().secret_key.encode()).digest())
    return Fernet(key).encrypt(json.dumps(details, separators=(",", ":")).encode()).decode()

def withdrawal_rule(user: User, amount_usd: Decimal, method: str, economy: dict, now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    if not user.phone_verified:
        raise ValueError("Phone verification is required")
    if now - user.created_at < timedelta(days=7):
        raise ValueError("Account must be at least 7 days old")
    if method not in {"mobile_wallet", "bank", "gift_card"}:
        raise ValueError("Unsupported payout method")
    if amount_usd < Decimal(str(economy["min_withdrawal_amount"])):
        raise ValueError("Below minimum withdrawal amount")
    return int(amount_usd * Decimal(str(economy["coin_to_currency_rate"])))

@router.get("/wallet")
async def wallet(user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    wallet = await get_or_create_wallet(db, user.id)
    economy = await economy_settings(db)
    return {"balance_coins": wallet.balance_coins, "estimated_usd": round(wallet.balance_coins / economy["coin_to_currency_rate"], 2), "frozen": wallet.frozen}

@router.get("/wallet/ledger")
async def ledger(limit: int = Query(default=50, ge=1, le=200), user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    entries = (await db.execute(select(CoinLedger).where(CoinLedger.user_id == user.id).order_by(CoinLedger.created_at.desc()).limit(limit))).scalars().all()
    return [{"id": str(x.id), "amount": x.amount, "entry_type": x.entry_type, "reference_id": x.reference_id,
             "balance_after": x.balance_after, "created_at": x.created_at.isoformat()} for x in entries]

@router.get("/ads/config")
async def ad_config(db: AsyncSession = Depends(get_db)):
    config = await db.get(AdConfig, 1)
    return {"in_feed_frequency": config.in_feed_frequency if config else 5,
            "daily_reward_cap": config.daily_reward_cap if config else 10,
            "cooldown_seconds": config.cooldown_seconds if config else 60}

@router.get("/ads/rewarded/status")
async def rewarded_status(user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    config = await db.get(AdConfig, 1)
    cap = config.daily_reward_cap if config else 10
    cooldown = config.cooldown_seconds if config else 60
    today = datetime.now(timezone.utc).date()
    count = await db.scalar(select(func.count(RewardedAdEvent.id)).where(RewardedAdEvent.user_id == user.id,
        RewardedAdEvent.verified.is_(True), func.date(RewardedAdEvent.created_at) == today))
    latest = await db.scalar(select(RewardedAdEvent).where(RewardedAdEvent.user_id == user.id,
        RewardedAdEvent.verified.is_(True)).order_by(RewardedAdEvent.created_at.desc()))
    remaining = max(0, cap - int(count or 0))
    cooldown_remaining = 0
    if latest:
        cooldown_remaining = max(0, cooldown - int((datetime.now(timezone.utc) - latest.created_at).total_seconds()))
    return {"remaining_today": remaining, "cooldown_remaining_seconds": cooldown_remaining, "eligible": remaining > 0 and cooldown_remaining == 0}

@router.get("/ads/ssv-callback")
async def rewarded_ssv(request: Request, db: AsyncSession = Depends(get_db)):
    params = dict(request.query_params)
    if not await verify_ssv_signature(params):
        raise HTTPException(400, "Invalid SSV signature")
    transaction_id = params.get("transaction_id")
    custom_data = params.get("custom_data")
    if not transaction_id or not custom_data:
        raise HTTPException(400, "Missing transaction or custom data")
    existing = await db.scalar(select(RewardedAdEvent).where(RewardedAdEvent.transaction_id == transaction_id))
    if existing:
        return {"ok": True, "duplicate": True}
    try:
        user_id = UUID(custom_data)
        reward = int(params.get("reward_amount", "0"))
        ad_unit_id = params.get("ad_unit", "")
    except (ValueError, TypeError) as exc:
        raise HTTPException(400, "Invalid SSV payload") from exc
    settings = await economy_settings(db)
    expected = int(settings["coins_per_rewarded_ad"])
    if reward <= 0:
        raise HTTPException(400, "Invalid reward amount")
    event = RewardedAdEvent(user_id=user_id, transaction_id=transaction_id, ad_unit_id=ad_unit_id,
                           verified=True, reward_coins=expected)
    db.add(event)
    await db.flush()
    try:
        await issue_coins(db, user_id, expected, "rewarded_ad", transaction_id, f"ad:{transaction_id}")
        referral = await db.scalar(select(Referral).where(Referral.referred_id == user_id).with_for_update())
        if referral and not referral.qualified_at:
            referral.rewarded_ads += 1
            await qualify_if_ready(db, referral)
        await db.commit()
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(409, str(exc)) from exc
    return {"ok": True}

@router.post("/wallet/checkin", response_model=CheckinResponse)
async def checkin(user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    today = datetime.now(timezone.utc).date()
    existing = await db.scalar(select(DailyCheckin).where(DailyCheckin.user_id == user.id))
    if existing and existing.checkin_date.date() == today:
        return CheckinResponse(coins=0, streak=existing.streak)
    streak = 1
    if existing and (today - existing.checkin_date.date()).days == 1:
        streak = min(existing.streak + 1, 7)
    if existing:
        existing.checkin_date = datetime.now(timezone.utc)
        existing.streak = streak
    else:
        db.add(DailyCheckin(user_id=user.id, checkin_date=datetime.now(timezone.utc), streak=streak))
    settings = await economy_settings(db)
    coins = int(settings["daily_checkin_coins"][streak - 1])
    try:
        await issue_coins(db, user.id, coins, "daily_checkin", today.isoformat(), f"checkin:{user.id}:{today}")
        await db.commit()
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(409, str(exc)) from exc
    return CheckinResponse(coins=coins, streak=streak)

@router.get("/referral/code")
async def referral_code(user: User = Depends(current_user)):
    return {"code": user.referral_code}

@router.post("/referral/apply")
async def apply_referral(payload: ReferralApplyRequest, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    referrer = await db.scalar(select(User).where(User.referral_code == payload.code.upper()))
    if not referrer or referrer.id == user.id:
        raise HTTPException(400, "Invalid referral code")
    existing = await db.scalar(select(Referral).where(Referral.referred_id == user.id))
    if existing:
        raise HTTPException(409, "Referral already applied")
    db.add(Referral(referrer_id=referrer.id, referred_id=user.id))
    await db.commit()
    return {"applied": True}

@router.post("/wallet/withdraw")
async def withdraw(payload: WithdrawalRequestModel, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    economy = await economy_settings(db)
    prior = await db.scalar(select(WithdrawalRequest).where(
        WithdrawalRequest.user_id == user.id, WithdrawalRequest.idempotency_key == payload.idempotency_key
    ))
    if prior:
        return {"id": prior.id, "status": prior.status.value, "amount_coins": prior.amount_coins}
    try:
        coins = withdrawal_rule(user, payload.amount_usd, payload.method, economy)
    except ValueError as exc:
        raise HTTPException(403 if "required" in str(exc) or "old" in str(exc) else 422, str(exc)) from exc
    try:
        await debit_coins(db, user.id, coins, "withdrawal_hold", idempotency_key=payload.idempotency_key)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    payout = PayoutMethod(user_id=user.id, method=payload.method, encrypted_details=encrypt_details(payload.details))
    db.add(payout)
    await db.flush()
    request_row = WithdrawalRequest(user_id=user.id, amount_coins=coins, status=WithdrawalStatus.pending,
                                    idempotency_key=payload.idempotency_key)
    db.add(request_row)
    await db.commit()
    return {"id": request_row.id, "status": request_row.status.value, "amount_coins": coins}

@router.get("/wallet/withdrawals")
async def withdrawals(user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(WithdrawalRequest).where(WithdrawalRequest.user_id == user.id).order_by(WithdrawalRequest.created_at.desc()))).scalars().all()
    return [{"id": str(x.id), "amount_coins": x.amount_coins, "status": x.status.value, "rejection_reason": x.rejection_reason,
             "created_at": x.created_at.isoformat()} for x in rows]
