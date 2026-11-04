import asyncio
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models import Role, AdminUser, AppSetting, AdConfig
from app.core.config import get_settings
from app.core.security import hash_password

ECONOMY = {
    "coins_per_rewarded_ad": 10,
    "coin_to_currency_rate": 1000,
    "min_withdrawal_amount": 2,
    "daily_checkin_coins": [1, 2, 3, 4, 5, 6, 7],
    "referral_bonus": 50,
    "creator_reward_per_1000_valid_views": 10,
    "payout_budget_percent": 50,
}

async def main():
    async with SessionLocal() as db:
        role = await db.scalar(select(Role).where(Role.name == "Super Admin"))
        if not role:
            role = Role(name="Super Admin", permissions=["*"])
            db.add(role)
            await db.flush()
        admin = await db.scalar(select(AdminUser).where(AdminUser.email == get_settings().admin_email))
        if not admin:
            db.add(AdminUser(email=get_settings().admin_email,
                             password_hash=hash_password(get_settings().admin_password),
                             role_id=role.id))
        config = await db.get(AdConfig, 1)
        if not config:
            db.add(AdConfig(id=1))
        economy = await db.get(AppSetting, "economy")
        if not economy:
            db.add(AppSetting(key="economy", value=ECONOMY, version=1))
        else:
            economy.value = {**ECONOMY, **economy.value}
            economy.version += 1
        await db.commit()
if __name__=="__main__": asyncio.run(main())
