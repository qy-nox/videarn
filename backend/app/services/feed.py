from datetime import datetime, timezone
from math import exp
from sqlalchemy import Select, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Block, Follow, Like, Video, VideoStats, VideoStatus, VideoView

class FeedService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_feed(self, user_id, following_only: bool, cursor: datetime | None, limit: int):
        blocked = select(Block.blocked_id).where(Block.blocker_id == user_id)
        seen = select(VideoView.video_id).where(VideoView.user_id == user_id)
        query: Select = (
            select(Video, VideoStats)
            .outerjoin(VideoStats, VideoStats.video_id == Video.id)
            .where(Video.status == VideoStatus.published, Video.privacy == "public",
                   Video.creator_id.not_in(blocked), Video.id.not_in(seen))
        )
        if following_only:
            followed = select(Follow.following_id).where(Follow.follower_id == user_id)
            query = query.where(Video.creator_id.in_(followed))
        if cursor:
            query = query.where(Video.created_at < cursor)
        query = query.order_by(desc(Video.created_at)).limit(limit)
        rows = (await self.db.execute(query)).all()
        return [self.serialize(video, stats) for video, stats in rows]

    @staticmethod
    def score(stats: VideoStats | None, created_at: datetime) -> float:
        if not stats:
            return 0.0
        age_hours = max((datetime.now(timezone.utc) - created_at).total_seconds() / 3600, 0)
        engagement = stats.likes + (stats.comments * 2) + (stats.shares * 3)
        return engagement * exp(-age_hours / 72)

    @staticmethod
    def serialize(video: Video, stats: VideoStats | None) -> dict:
        return {
            "id": str(video.id), "creator_id": str(video.creator_id), "caption": video.caption,
            "status": video.status.value, "duration_seconds": video.duration_seconds,
            "thumbnail_url": video.thumbnail_url, "created_at": video.created_at.isoformat(),
            "stats": {"views": stats.views if stats else 0, "likes": stats.likes if stats else 0,
                      "comments": stats.comments if stats else 0, "shares": stats.shares if stats else 0},
        }
