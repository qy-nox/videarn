from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Referral, User
from app.services.economy import economy_settings, issue_coins

async def qualify_if_ready(db: AsyncSession, referral: Referral) -> bool:
    if referral.qualified_at or referral.watched_videos < 5 or referral.rewarded_ads < 1:
        return False
    settings = await economy_settings(db)
    now = datetime.now(timezone.utc)
    async with db.begin_nested():
        await issue_coins(db, referral.referrer_id, int(settings["referral_bonus"]), "referral_bonus",
                          str(referral.id), f"referral:{referral.id}")
        await issue_coins(db, referral.referred_id, int(settings["referral_bonus"]), "referral_bonus",
                          str(referral.id), f"referral:{referral.id}:referred")
    referral.qualified_at = now
    return True

async def record_video_progress(db: AsyncSession, user_id) -> None:
    referral = await db.scalar(select(Referral).where(Referral.referred_id == user_id).with_for_update())
    if referral and not referral.qualified_at:
        referral.watched_videos += 1
        try:
            await qualify_if_ready(db, referral)
        except ValueError:
            # Keep progress recorded; qualification will retry on the next qualifying event.
            pass
