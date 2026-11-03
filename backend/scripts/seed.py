import asyncio
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models import Role, AdminUser, AppSetting, AdConfig
from app.core.config import get_settings
from app.core.security import hash_password
async def main():
    async with SessionLocal() as db:
        if not await db.scalar(select(Role).where(Role.name=="Super Admin")): db.add(Role(name="Super Admin",permissions=["*"]))
        role=await db.scalar(select(Role).where(Role.name=="Super Admin"))
        if not await db.scalar(select(AdminUser).where(AdminUser.email==get_settings().admin_email)): db.add(AdminUser(email=get_settings().admin_email,password_hash=hash_password(get_settings().admin_password),role_id=role.id))
        db.add(AdConfig()); db.add_all([AppSetting(key="economy",value={"coins_per_rewarded_ad":10,"coin_to_currency_rate":1000,"min_withdrawal_amount":2,"daily_checkin_coins":[1,2,3,4,5,6,7],"referral_bonus":50,"creator_reward_per_1000_valid_views":10,"payout_budget_percent":50})]); await db.commit()
if __name__=="__main__": asyncio.run(main())
