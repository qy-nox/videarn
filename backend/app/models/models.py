import enum, uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, JSON, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class UserStatus(str, enum.Enum):
    active="active"; suspended="suspended"; banned="banned"; deleted="deleted"
class VideoStatus(str, enum.Enum):
    processing="processing"; pending_review="pending_review"; published="published"; rejected="rejected"; removed="removed"
class WithdrawalStatus(str, enum.Enum):
    pending="pending"; approved="approved"; paid="paid"; rejected="rejected"

class Timestamped:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class User(Timestamped, Base):
    __tablename__="users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    firebase_uid: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    phone: Mapped[str|None] = mapped_column(String(32), unique=True)
    email: Mapped[str|None] = mapped_column(String(320), unique=True)
    username: Mapped[str|None] = mapped_column(String(32), unique=True, index=True)
    status: Mapped[UserStatus] = mapped_column(Enum(UserStatus), default=UserStatus.active, index=True)
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    birth_date: Mapped[datetime|None] = mapped_column(DateTime(timezone=True))
    terms_accepted_at: Mapped[datetime|None] = mapped_column(DateTime(timezone=True))
    privacy_accepted_at: Mapped[datetime|None] = mapped_column(DateTime(timezone=True))
    fraud_score: Mapped[int] = mapped_column(Integer, default=0)

class UserProfile(Timestamped, Base):
    __tablename__="user_profiles"
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    display_name: Mapped[str|None] = mapped_column(String(80)); bio: Mapped[str|None] = mapped_column(Text)
    avatar_url: Mapped[str|None] = mapped_column(Text); country: Mapped[str|None] = mapped_column(String(2))

class Device(Timestamped, Base):
    __tablename__="devices"; __table_args__=(UniqueConstraint("user_id","fingerprint"), Index("ix_devices_fingerprint","fingerprint"))
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    fingerprint: Mapped[str] = mapped_column(String(128)); fcm_token: Mapped[str|None] = mapped_column(Text)
    integrity_ok: Mapped[bool] = mapped_column(Boolean, default=False); last_ip: Mapped[str|None] = mapped_column(String(64))

class AuthSession(Timestamped, Base):
    __tablename__="auth_sessions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    refresh_token_hash: Mapped[str] = mapped_column(String(128), unique=True); expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True)); revoked_at: Mapped[datetime|None] = mapped_column(DateTime(timezone=True))

class Role(Base):
    __tablename__="roles"; id: Mapped[int] = mapped_column(primary_key=True); name: Mapped[str] = mapped_column(String(40), unique=True); permissions: Mapped[list] = mapped_column(JSON, default=list)
class AdminUser(Base):
    __tablename__="admin_users"; id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4); email: Mapped[str] = mapped_column(String(320), unique=True); password_hash: Mapped[str]; totp_secret: Mapped[str|None]; is_active: Mapped[bool] = mapped_column(Boolean, default=True); role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))

class Video(Timestamped, Base):
    __tablename__="videos"; __table_args__=(Index("ix_videos_status_created","status","created_at"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4); creator_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id")); caption: Mapped[str|None] = mapped_column(Text); status: Mapped[VideoStatus] = mapped_column(Enum(VideoStatus), default=VideoStatus.processing, index=True); privacy: Mapped[str] = mapped_column(String(16), default="public"); duration_seconds: Mapped[int]; source_key: Mapped[str]; thumbnail_url: Mapped[str|None] = mapped_column(Text); is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
class VideoAsset(Base):
    __tablename__="video_assets"; id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4); video_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE")); quality: Mapped[str] = mapped_column(String(8)); playlist_url: Mapped[str]; width: Mapped[int]; height: Mapped[int]
class VideoStats(Base):
    __tablename__="video_stats"; video_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), primary_key=True); views: Mapped[int]=mapped_column(Integer,default=0); likes: Mapped[int]=mapped_column(Integer,default=0); comments: Mapped[int]=mapped_column(Integer,default=0); shares: Mapped[int]=mapped_column(Integer,default=0)
class VideoView(Base):
    __tablename__="video_views"; __table_args__=(UniqueConstraint("user_id","video_id","view_date"), Index("ix_video_views_video","video_id"))
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4); user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id")); video_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("videos.id")); view_date: Mapped[datetime] = mapped_column(DateTime(timezone=True)); watched_seconds: Mapped[int]; watch_ratio: Mapped[float]

class Like(Base): __tablename__="likes"; user_id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("users.id"),primary_key=True); video_id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("videos.id"),primary_key=True)
class Comment(Timestamped, Base): __tablename__="comments"; id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4); user_id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("users.id")); video_id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("videos.id")); parent_id: Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True),ForeignKey("comments.id")); body: Mapped[str]=mapped_column(Text); deleted: Mapped[bool]=mapped_column(Boolean,default=False)
class CommentLike(Base): __tablename__="comment_likes"; user_id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("users.id"),primary_key=True); comment_id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("comments.id"),primary_key=True)
class Follow(Base): __tablename__="follows"; follower_id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("users.id"),primary_key=True); following_id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("users.id"),primary_key=True)
class Block(Base): __tablename__="blocks"; blocker_id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("users.id"),primary_key=True); blocked_id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("users.id"),primary_key=True)
class Hashtag(Base): __tablename__="hashtags"; id: Mapped[int]=mapped_column(primary_key=True); name: Mapped[str]=mapped_column(String(80),unique=True,index=True)
class VideoHashtag(Base): __tablename__="video_hashtags"; video_id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("videos.id"),primary_key=True); hashtag_id: Mapped[int]=mapped_column(ForeignKey("hashtags.id"),primary_key=True)
class Sound(Base): __tablename__="sounds"; id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4); name: Mapped[str]; storage_key: Mapped[str]; licensed: Mapped[bool]=mapped_column(Boolean,default=False); enabled: Mapped[bool]=mapped_column(Boolean,default=True)
class Report(Timestamped, Base): __tablename__="reports"; id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4); reporter_id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("users.id")); target_type: Mapped[str]; target_id: Mapped[uuid.UUID]; reason: Mapped[str]; status: Mapped[str]=mapped_column(String(16),default="open")
class Notification(Timestamped, Base): __tablename__="notifications"; id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4); user_id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("users.id")); title: Mapped[str]; body: Mapped[str]; read_at: Mapped[datetime|None]
class Wallet(Timestamped, Base): __tablename__="wallets"; user_id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("users.id"),primary_key=True); balance_coins: Mapped[int]=mapped_column(Integer,default=0); frozen: Mapped[bool]=mapped_column(Boolean,default=False)
class CoinLedger(Timestamped, Base): __tablename__="coin_ledger"; id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4); user_id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("users.id"),index=True); amount: Mapped[int]; entry_type: Mapped[str]; reference_id: Mapped[str|None]; idempotency_key: Mapped[str|None]=mapped_column(String(128),unique=True); balance_after: Mapped[int]
class RewardedAdEvent(Timestamped, Base): __tablename__="rewarded_ad_events"; id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4); user_id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("users.id")); transaction_id: Mapped[str]=mapped_column(String(256),unique=True); ad_unit_id: Mapped[str]; verified: Mapped[bool]=mapped_column(Boolean,default=False); reward_coins: Mapped[int]=mapped_column(Integer,default=0)
class DailyCheckin(Base): __tablename__="daily_checkins"; user_id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("users.id"),primary_key=True); checkin_date: Mapped[datetime]; streak: Mapped[int]
class Referral(Base): __tablename__="referrals"; id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4); referrer_id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("users.id")); referred_id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("users.id"),unique=True); qualified_at: Mapped[datetime|None]
class PayoutMethod(Base): __tablename__="payout_methods"; id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4); user_id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("users.id")); method: Mapped[str]; encrypted_details: Mapped[str]
class WithdrawalRequest(Timestamped, Base): __tablename__="withdrawal_requests"; id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4); user_id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("users.id")); amount_coins: Mapped[int]; status: Mapped[WithdrawalStatus]=mapped_column(Enum(WithdrawalStatus),default=WithdrawalStatus.pending); rejection_reason: Mapped[str|None]
class FraudFlag(Timestamped, Base): __tablename__="fraud_flags"; id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4); user_id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),ForeignKey("users.id")); reason: Mapped[str]; score: Mapped[int]; resolved_at: Mapped[datetime|None]
class AppSetting(Timestamped, Base): __tablename__="app_settings"; key: Mapped[str]=mapped_column(String(100),primary_key=True); value: Mapped[dict]=mapped_column(JSON); version: Mapped[int]=mapped_column(Integer,default=1)
class AdConfig(Base): __tablename__="ad_config"; id: Mapped[int]=mapped_column(primary_key=True,default=1); in_feed_frequency: Mapped[int]=mapped_column(Integer,default=5); daily_reward_cap: Mapped[int]=mapped_column(Integer,default=10); cooldown_seconds: Mapped[int]=mapped_column(Integer,default=60)
class Announcement(Timestamped, Base): __tablename__="announcements"; id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4); title: Mapped[str]; body: Mapped[str]; published: Mapped[bool]=mapped_column(Boolean,default=False)
class AuditLog(Timestamped, Base): __tablename__="audit_logs"; id: Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4); admin_id: Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True),ForeignKey("admin_users.id")); action: Mapped[str]; entity_type: Mapped[str]; entity_id: Mapped[str|None]; before: Mapped[dict|None]=mapped_column(JSON); after: Mapped[dict|None]=mapped_column(JSON); ip: Mapped[str|None]
class FeatureFlag(Base): __tablename__="feature_flags"; key: Mapped[str]=mapped_column(String(100),primary_key=True); enabled: Mapped[bool]=mapped_column(Boolean,default=False); metadata_json: Mapped[dict]=mapped_column(JSON,default=dict)
