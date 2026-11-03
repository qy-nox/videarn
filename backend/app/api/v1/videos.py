from datetime import datetime, timezone
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import current_user
from app.db.session import get_db
from app.models import Block, Comment, Follow, Like, User, Video, VideoStats, VideoStatus, VideoView
from app.schemas.videos import (
    CommentCreateRequest, UploadURLRequest, UploadURLResponse, VideoCreateRequest,
    ViewBatchRequest,
)
from app.services.feed import FeedService
from app.services.storage import StorageService

router = APIRouter(tags=["videos"])

@router.post("/videos/upload-url", response_model=UploadURLResponse)
async def upload_url(payload: UploadURLRequest, user: User = Depends(current_user)):
    key = f"uploads/{user.id}/{uuid4()}-{payload.filename}"
    try:
        url = StorageService().presigned_upload(key, payload.content_type)
    except Exception as exc:
        raise HTTPException(503, "Video storage is unavailable") from exc
    return UploadURLResponse(upload_url=url, source_key=key, expires_in=900)

@router.post("/videos", status_code=status.HTTP_202_ACCEPTED)
async def create_video(payload: VideoCreateRequest, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    video = Video(creator_id=user.id, source_key=payload.source_key, duration_seconds=payload.duration_seconds,
                  caption=payload.caption, privacy=payload.privacy, status=VideoStatus.processing)
    db.add(video)
    db.add(VideoStats(video_id=video.id))
    await db.commit()
    from app.worker import transcode_video
    transcode_video.delay(str(video.id))
    return {"id": video.id, "status": video.status.value}

@router.get("/feed/for-you")
async def for_you(cursor: datetime | None = Query(default=None), limit: int = Query(default=20, ge=1, le=50),
                   user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    return await FeedService(db).get_feed(user.id, False, cursor, limit)

@router.get("/feed/following")
async def following(cursor: datetime | None = Query(default=None), limit: int = Query(default=20, ge=1, le=50),
                    user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    return await FeedService(db).get_feed(user.id, True, cursor, limit)

@router.get("/videos/{video_id}")
async def get_video(video_id, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    row = (await db.execute(select(Video, VideoStats).outerjoin(VideoStats, VideoStats.video_id == Video.id)
                            .where(Video.id == video_id))).first()
    if not row or row[0].status != VideoStatus.published and row[0].creator_id != user.id:
        raise HTTPException(404, "Video not found")
    return FeedService.serialize(*row)

@router.get("/users/{user_id}/videos")
async def user_videos(user_id, cursor: datetime | None = Query(default=None),
                      limit: int = Query(default=20, ge=1, le=50),
                      _: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    query = select(Video, VideoStats).outerjoin(VideoStats, VideoStats.video_id == Video.id).where(
        Video.creator_id == user_id, Video.status == VideoStatus.published, Video.privacy == "public"
    )
    if cursor:
        query = query.where(Video.created_at < cursor)
    rows = (await db.execute(query.order_by(Video.created_at.desc()).limit(limit))).all()
    return [FeedService.serialize(video, stats) for video, stats in rows]

@router.get("/videos/{video_id}/comments")
async def list_comments(video_id, limit: int = Query(default=50, ge=1, le=100),
                        _: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    comments = (await db.execute(select(Comment).where(
        Comment.video_id == video_id, Comment.deleted.is_(False)
    ).order_by(Comment.created_at.asc()).limit(limit))).scalars().all()
    return [{"id": str(comment.id), "user_id": str(comment.user_id), "parent_id": str(comment.parent_id) if comment.parent_id else None,
             "body": comment.body, "created_at": comment.created_at.isoformat()} for comment in comments]

@router.get("/search")
async def search(q: str = Query(min_length=1, max_length=80),
                 _: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    pattern = f"%{q.strip()}%"
    users = (await db.execute(select(User).where(User.status == "active", User.username.ilike(pattern)).limit(20))).scalars().all()
    videos = (await db.execute(select(Video, VideoStats).outerjoin(VideoStats, VideoStats.video_id == Video.id).where(
        Video.status == VideoStatus.published, Video.caption.ilike(pattern)
    ).order_by(Video.created_at.desc()).limit(20))).all()
    return {"users": [{"id": str(item.id), "username": item.username} for item in users],
            "videos": [FeedService.serialize(video, stats) for video, stats in videos]}

@router.delete("/videos/{video_id}")
async def delete_video(video_id, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    video = await db.scalar(select(Video).where(Video.id == video_id, Video.creator_id == user.id))
    if not video:
        raise HTTPException(404, "Video not found")
    video.status = VideoStatus.removed
    await db.commit()
    return {"ok": True}

@router.post("/videos/{video_id}/like")
async def like(video_id, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    video = await db.scalar(select(Video).where(Video.id == video_id, Video.status == VideoStatus.published))
    if not video: raise HTTPException(404, "Video not found")
    existing = await db.scalar(select(Like).where(Like.user_id == user.id, Like.video_id == video.id))
    if not existing:
        db.add(Like(user_id=user.id, video_id=video.id))
        await db.execute(update(VideoStats).where(VideoStats.video_id == video.id).values(likes=VideoStats.likes + 1))
        await db.commit()
    return {"liked": True}

@router.delete("/videos/{video_id}/like")
async def unlike(video_id, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(delete(Like).where(Like.user_id == user.id, Like.video_id == video_id))
    if result.rowcount:
        await db.execute(update(VideoStats).where(VideoStats.video_id == video_id).values(likes=func.greatest(VideoStats.likes - 1, 0)))
        await db.commit()
    return {"liked": False}

@router.post("/videos/{video_id}/comments")
async def add_comment(video_id, payload: CommentCreateRequest, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    video = await db.scalar(select(Video).where(Video.id == video_id, Video.status == VideoStatus.published))
    if not video: raise HTTPException(404, "Video not found")
    if payload.parent_id:
        parent = await db.scalar(select(Comment).where(Comment.id == payload.parent_id, Comment.video_id == video.id, Comment.parent_id.is_(None)))
        if not parent: raise HTTPException(400, "Only one nested comment level is supported")
    comment = Comment(user_id=user.id, video_id=video.id, parent_id=payload.parent_id, body=payload.body)
    db.add(comment)
    await db.execute(update(VideoStats).where(VideoStats.video_id == video.id).values(comments=VideoStats.comments + 1))
    await db.commit()
    return {"id": comment.id, "body": comment.body}

@router.delete("/comments/{comment_id}")
async def delete_comment(comment_id, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    comment = await db.scalar(select(Comment).where(Comment.id == comment_id, Comment.user_id == user.id, Comment.deleted.is_(False)))
    if not comment: raise HTTPException(404, "Comment not found")
    comment.deleted = True
    await db.commit()
    return {"ok": True}

@router.post("/users/{target_id}/follow")
async def follow(target_id, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    if str(target_id) == str(user.id): raise HTTPException(400, "Cannot follow yourself")
    target = await db.get(User, target_id)
    if not target or target.status.value != "active": raise HTTPException(404, "User not found")
    db.add(Follow(follower_id=user.id, following_id=target.id))
    await db.commit()
    return {"following": True}

@router.delete("/users/{target_id}/follow")
async def unfollow(target_id, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    await db.execute(delete(Follow).where(Follow.follower_id == user.id, Follow.following_id == target_id))
    await db.commit()
    return {"following": False}

@router.post("/users/{target_id}/block")
async def block(target_id, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    if str(target_id) == str(user.id): raise HTTPException(400, "Cannot block yourself")
    db.add(Block(blocker_id=user.id, blocked_id=target_id))
    await db.commit()
    return {"blocked": True}

@router.post("/videos/{video_id}/view")
async def view_batch(video_id, payload: ViewBatchRequest, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    events = [event for event in payload.events if str(event.video_id) == str(video_id)]
    if not events: raise HTTPException(400, "No matching view events")
    video = await db.scalar(select(Video).where(Video.id == video_id, Video.status == VideoStatus.published))
    if not video: raise HTTPException(404, "Video not found")
    today = datetime.now(timezone.utc).date()
    existing = await db.scalar(select(VideoView).where(VideoView.user_id == user.id, VideoView.video_id == video.id,
                                                       func.date(VideoView.view_date) == today))
    if existing: return {"counted": False, "reason": "already_counted_today"}
    best = max(events, key=lambda event: event.watched_seconds)
    if best.watched_seconds < 5 and best.watch_ratio < 0.5:
        return {"counted": False, "reason": "minimum_watch_not_met"}
    db.add(VideoView(user_id=user.id, video_id=video.id, view_date=datetime.now(timezone.utc),
                     watched_seconds=best.watched_seconds, watch_ratio=best.watch_ratio))
    await db.execute(update(VideoStats).where(VideoStats.video_id == video.id).values(views=VideoStats.views + 1))
    from app.services.referrals import record_video_progress
    await record_video_progress(db, user.id)
    await db.commit()
    return {"counted": True}
