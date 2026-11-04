"""phase 3 wallet and fraud fields"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

def upgrade():
    inspector = sa.inspect(op.get_bind())
    users = {column["name"] for column in inspector.get_columns("users")}
    if "referral_code" not in users:
        op.add_column("users", sa.Column("referral_code", sa.String(16), nullable=True))
    if "ix_users_referral_code" not in {index["name"] for index in inspector.get_indexes("users")}:
        op.create_index("ix_users_referral_code", "users", ["referral_code"], unique=True)
    referrals = {column["name"] for column in inspector.get_columns("referrals")}
    if "watched_videos" not in referrals:
        op.add_column("referrals", sa.Column("watched_videos", sa.Integer(), server_default="0", nullable=False))
    if "rewarded_ads" not in referrals:
        op.add_column("referrals", sa.Column("rewarded_ads", sa.Integer(), server_default="0", nullable=False))
    if "payout_budgets" not in inspector.get_table_names():
        op.create_table(
            "payout_budgets",
            sa.Column("budget_date", sa.DateTime(timezone=True), primary_key=True),
            sa.Column("estimated_revenue_usd", sa.Numeric(12, 2), nullable=False, server_default="0"),
            sa.Column("issued_coins", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("budget_percent", sa.Numeric(5, 2), nullable=False, server_default="50"),
            sa.Column("paused", sa.Boolean(), nullable=False, server_default=sa.false()),
        )
    withdrawals = {column["name"] for column in inspector.get_columns("withdrawal_requests")}
    if "idempotency_key" not in withdrawals:
        op.add_column("withdrawal_requests", sa.Column("idempotency_key", sa.String(128), nullable=True))
        op.create_unique_constraint("uq_withdrawal_requests_idempotency_key", "withdrawal_requests", ["idempotency_key"])

def downgrade():
    op.drop_table("payout_budgets")
    op.drop_constraint("uq_withdrawal_requests_idempotency_key", "withdrawal_requests", type_="unique")
    op.drop_column("withdrawal_requests", "idempotency_key")
    op.drop_column("referrals", "rewarded_ads")
    op.drop_column("referrals", "watched_videos")
    op.drop_index("ix_users_referral_code", table_name="users")
    op.drop_column("users", "referral_code")
