from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, field_validator

class UploadURLRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(pattern=r"^video/(mp4|quicktime|webm)$")
    size_bytes: int = Field(gt=0, le=100 * 1024 * 1024)

class UploadURLResponse(BaseModel):
    upload_url: str
    source_key: str
    expires_in: int

class VideoCreateRequest(BaseModel):
    source_key: str = Field(min_length=5, max_length=512)
    duration_seconds: int = Field(ge=15, le=90)
    caption: str | None = Field(default=None, max_length=2200)
    privacy: str = "public"

    @field_validator("privacy")
    @classmethod
    def valid_privacy(cls, value: str) -> str:
        if value not in {"public", "followers", "private"}:
            raise ValueError("privacy must be public, followers, or private")
        return value

class VideoResponse(BaseModel):
    id: UUID
    creator_id: UUID
    caption: str | None
    status: str
    duration_seconds: int
    thumbnail_url: str | None
    created_at: datetime
    stats: dict

class ViewEvent(BaseModel):
    video_id: UUID
    watched_seconds: int = Field(ge=0, le=90)
    watch_ratio: float = Field(ge=0, le=1)

class ViewBatchRequest(BaseModel):
    events: list[ViewEvent] = Field(min_length=1, max_length=50)

class CommentCreateRequest(BaseModel):
    body: str = Field(min_length=1, max_length=1000)
    parent_id: UUID | None = None
