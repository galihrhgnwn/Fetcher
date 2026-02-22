"""
Base extractor interface — the plugin contract every extractor must implement.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Callable, Awaitable, Optional
from backend.models import VideoMetadata


# Progress callback type: (progress_pct, speed, eta, message) → None
ProgressCallback = Callable[[float, Optional[str], Optional[str], Optional[str]], Awaitable[None]]


class DownloadResult:
    __slots__ = ("file_path", "filename", "file_size", "extractor_used")

    def __init__(
        self,
        file_path: str,
        filename: str,
        file_size: Optional[int] = None,
        extractor_used: str = "unknown",
    ):
        self.file_path      = file_path
        self.filename       = filename
        self.file_size      = file_size
        self.extractor_used = extractor_used


class IExtractor(ABC):
    """
    Plugin contract for all media extractors.

    Attributes:
        name     — unique identifier, e.g. "yt-dlp"
        priority — higher value = preferred when multiple extractors match.
                   direct-file = 5, yt-dlp = 10, custom = 15+
    """
    name:     str
    priority: int

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """Return True if this extractor supports the given URL."""

    @abstractmethod
    async def get_metadata(self, url: str, cookie_file: Optional[str] = None) -> VideoMetadata:
        """Fetch and return video/audio metadata without downloading."""

    @abstractmethod
    async def download(
        self,
        url:          str,
        format:       str,
        quality:      str,
        output_dir:   str,
        job_id:       str,
        progress_cb:  ProgressCallback,
        cookie_file:  Optional[str] = None,
    ) -> DownloadResult:
        """
        Download (and optionally convert) the media.
        Must call progress_cb periodically with (pct, speed, eta, message).
        Returns a DownloadResult with the final file path.
        """

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r} priority={self.priority}>"
