"""
Pydantic models — shared request/response types for the entire application.
"""
from __future__ import annotations
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, HttpUrl, field_validator


# ─── Enums ────────────────────────────────────────────────────────────────────

class JobStatus(str, Enum):
    QUEUED            = "queued"
    FETCHING_METADATA = "fetching_metadata"
    DOWNLOADING       = "downloading"
    CONVERTING        = "converting"
    DONE              = "done"
    ERROR             = "error"
    CANCELLED         = "cancelled"


class UrlType(str, Enum):
    YOUTUBE      = "youtube"
    TIKTOK       = "tiktok"
    INSTAGRAM    = "instagram"
    TWITTER      = "twitter"
    FACEBOOK     = "facebook"
    VIMEO        = "vimeo"
    TWITCH       = "twitch"
    SOUNDCLOUD   = "soundcloud"
    REDDIT       = "reddit"
    DAILYMOTION  = "dailymotion"
    BILIBILI     = "bilibili"
    DIRECT_FILE  = "direct_file"
    GENERIC_WEB  = "generic_web"


# ─── Requests ─────────────────────────────────────────────────────────────────

class MetadataRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def strip_url(cls, v: str) -> str:
        return v.strip()


class StartDownloadRequest(BaseModel):
    url: str
    format: str = "mp4"
    quality: str = "best"

    @field_validator("url")
    @classmethod
    def strip_url(cls, v: str) -> str:
        return v.strip()

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        allowed = {"mp4", "mp3", "webm", "mkv", "m4a", "opus", "flac", "wav", "best"}
        v = v.lower()
        if v not in allowed:
            raise ValueError(f"Format must be one of: {', '.join(sorted(allowed))}")
        return v

    @field_validator("quality")
    @classmethod
    def validate_quality(cls, v: str) -> str:
        allowed = {"best", "4320p", "2160p", "1440p", "1080p", "720p", "480p", "360p", "240p", "144p"}
        if v not in allowed:
            raise ValueError(f"Quality must be one of: {', '.join(sorted(allowed))}")
        return v


# ─── Responses ────────────────────────────────────────────────────────────────

class ValidateUrlResponse(BaseModel):
    valid: bool
    url_type: Optional[str] = None
    normalised: Optional[str] = None
    error: Optional[str] = None


class FormatOption(BaseModel):
    format_id: str
    ext: str
    quality: Optional[str] = None
    resolution: Optional[str] = None
    filesize: Optional[int] = None
    vcodec: Optional[str] = None
    acodec: Optional[str] = None
    note: Optional[str] = None


class VideoMetadata(BaseModel):
    title: str
    thumbnail: Optional[str] = None
    duration: Optional[int] = None          # seconds
    uploader: Optional[str] = None
    upload_date: Optional[str] = None
    view_count: Optional[int] = None
    description: Optional[str] = None
    formats: List[FormatOption] = []
    estimated_size: Optional[int] = None    # bytes
    is_audio_only: bool = False
    extractor: Optional[str] = None


class MetadataResponse(BaseModel):
    metadata: VideoMetadata
    url_type: Optional[str] = None


class StartDownloadResponse(BaseModel):
    job_id: str
    status: JobStatus


class JobStatusResponse(BaseModel):
    id: str
    url: str
    format: str
    quality: str
    status: JobStatus
    progress: float = 0.0
    speed: Optional[str] = None
    eta: Optional[str] = None
    filename: Optional[str] = None
    file_size: Optional[int] = None
    error: Optional[str] = None
    created_at: float
    updated_at: float


class CancelResponse(BaseModel):
    success: bool
    message: str


class SSEEvent(BaseModel):
    status: JobStatus
    progress: float = 0.0
    message: Optional[str] = None
    speed: Optional[str] = None
    eta: Optional[str] = None
    filename: Optional[str] = None
    file_size: Optional[int] = None
    error: Optional[str] = None
