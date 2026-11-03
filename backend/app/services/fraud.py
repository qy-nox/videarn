from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import FraudFlag, User, Wallet

FRAUD_THRESHOLD = 70

async def assess_user(db: AsyncSession, user_id, reason: str, points: int) -> int:
    user = await db.scalar(select(User).where(User.id == user_id).with_for_update())
    if not user:
        raise ValueError("User not found")
    user.fraud_score = min(100, user.fraud_score + points)
    if user.fraud_score >= FRAUD_THRESHOLD:
        wallet = await db.scalar(select(Wallet).where(Wallet.user_id == user_id).with_for_update())
        if wallet:
            wallet.frozen = True
        db.add(FraudFlag(user_id=user_id, reason=reason, score=user.fraud_score))
    await db.flush()
    return user.fraud_score
