from celery import Celery
import os
import subprocess
import tempfile
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models import Video, VideoAsset, VideoStatus
from app.services.storage import StorageService
from app.core.config import get_settings
celery_app=Celery("videarn",broker=get_settings().redis_url,backend=get_settings().redis_url)

@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def transcode_video(self, video_id: str):
    import asyncio
    return asyncio.run(_transcode_video(video_id))

async def _transcode_video(video_id: str):
    async with SessionLocal() as db:
        video = await db.scalar(select(Video).where(Video.id == video_id))
        if not video:
            return
        storage = StorageService()
        with tempfile.TemporaryDirectory() as workdir:
            source = os.path.join(workdir, "source.mp4")
            storage.download(video.source_key, source)
            output_dir = os.path.join(workdir, "hls")
            os.makedirs(output_dir)
            for quality, height, bitrate in (("360p", 360, "800k"), ("540p", 540, "1500k"), ("720p", 720, "2500k")):
                playlist = os.path.join(output_dir, f"{quality}.m3u8")
                subprocess.run([
                    "ffmpeg", "-y", "-i", source, "-vf", f"scale=-2:{height}", "-c:v", "libx264",
                    "-b:v", bitrate, "-c:a", "aac", "-b:a", "128k", "-f", "hls", "-hls_time", "4",
                    "-hls_playlist_type", "vod", playlist,
                ], check=True, capture_output=True)
                for filename in os.listdir(output_dir):
                    if filename.startswith(quality):
                        path = os.path.join(output_dir, filename)
                        storage.upload_file(path, f"videos/{video.id}/{filename}", "application/vnd.apple.mpegurl" if filename.endswith(".m3u8") else "video/mp2t")
                db.add(VideoAsset(video_id=video.id, quality=quality, playlist_url=storage.public_url(f"videos/{video.id}/{quality}.m3u8"), width=height * 9 // 16, height=height))
            thumb = os.path.join(workdir, "thumb.jpg")
            subprocess.run(["ffmpeg", "-y", "-i", source, "-frames:v", "1", thumb], check=True, capture_output=True)
            storage.upload_file(thumb, f"videos/{video.id}/thumbnail.jpg", "image/jpeg")
            video.thumbnail_url = storage.public_url(f"videos/{video.id}/thumbnail.jpg")
            video.status = VideoStatus.pending_review
            await db.commit()
