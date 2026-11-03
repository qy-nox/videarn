from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import AppSetting, CoinLedger, PayoutBudget, Wallet

DEFAULT_ECONOMY = {
    "coins_per_rewarded_ad": 10, "coin_to_currency_rate": 1000,
    "min_withdrawal_amount": 2, "daily_checkin_coins": [1, 2, 3, 4, 5, 6, 7],
    "referral_bonus": 50, "creator_reward_per_1000_valid_views": 10,
    "payout_budget_percent": 50,
}

async def economy_settings(db: AsyncSession) -> dict:
    setting = await db.scalar(select(AppSetting).where(AppSetting.key == "economy"))
    return {**DEFAULT_ECONOMY, **(setting.value if setting else {})}

async def get_or_create_wallet(db: AsyncSession, user_id, lock: bool = False) -> Wallet:
    query = select(Wallet).where(Wallet.user_id == user_id)
    if lock:
        query = query.with_for_update()
    wallet = await db.scalar(query)
    if not wallet:
        wallet = Wallet(user_id=user_id, balance_coins=0)
        db.add(wallet)
        await db.flush()
    return wallet

async def issue_coins(db: AsyncSession, user_id, amount: int, entry_type: str,
                      reference_id: str | None = None, idempotency_key: str | None = None) -> CoinLedger:
    if amount <= 0:
        raise ValueError("Coin issuance must be positive")
    if idempotency_key:
        existing = await db.scalar(select(CoinLedger).where(CoinLedger.idempotency_key == idempotency_key))
        if existing:
            return existing
    wallet = await get_or_create_wallet(db, user_id, lock=True)
    if wallet.frozen:
        raise ValueError("Wallet is frozen")
    budget = await today_budget(db, lock=True)
    economy = await economy_settings(db)
    max_coins = int(Decimal(str(budget.estimated_revenue_usd)) * Decimal(str(economy["coin_to_currency_rate"])
                    ) * Decimal(str(budget.budget_percent)) / Decimal("100"))
    if budget.paused or budget.issued_coins + amount > max_coins:
        budget.paused = True
        raise ValueError("Payout budget exceeded; rewards are paused")
    wallet.balance_coins += amount
    budget.issued_coins += amount
    entry = CoinLedger(user_id=user_id, amount=amount, entry_type=entry_type,
                       reference_id=reference_id, idempotency_key=idempotency_key,
                       balance_after=wallet.balance_coins)
    db.add(entry)
    await db.flush()
    return entry

async def debit_coins(db: AsyncSession, user_id, amount: int, entry_type: str,
                      reference_id: str | None = None, idempotency_key: str | None = None) -> CoinLedger:
    if amount <= 0:
        raise ValueError("Debit must be positive")
    if idempotency_key:
        existing = await db.scalar(select(CoinLedger).where(CoinLedger.idempotency_key == idempotency_key))
        if existing:
            return existing
    wallet = await get_or_create_wallet(db, user_id, lock=True)
    if wallet.frozen or wallet.balance_coins < amount:
        raise ValueError("Insufficient or frozen wallet balance")
    wallet.balance_coins -= amount
    entry = CoinLedger(user_id=user_id, amount=-amount, entry_type=entry_type,
                       reference_id=reference_id, idempotency_key=idempotency_key,
                       balance_after=wallet.balance_coins)
    db.add(entry)
    await db.flush()
    return entry

async def today_budget(db: AsyncSession, lock: bool = False) -> PayoutBudget:
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    query = select(PayoutBudget).where(PayoutBudget.budget_date == today)
    if lock:
        query = query.with_for_update()
    budget = await db.scalar(query)
    if not budget:
        economy = await economy_settings(db)
        budget = PayoutBudget(budget_date=today, budget_percent=economy["payout_budget_percent"])
        db.add(budget)
        await db.flush()
    return budget
