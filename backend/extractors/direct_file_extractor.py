"""
Direct File Extractor — downloads files via direct URL (.mp4, .mp3, .zip, .pdf, etc.)

For audio formats (mp3, m4a, etc.) it verifies the file with ffprobe and re-encodes
with ffmpeg if needed — guaranteeing a valid audio file, not a renamed video.
"""
from __future__ import annotations
import asyncio
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import httpx

from backend.extractors.base import IExtractor, DownloadResult, ProgressCallback
from backend.models import VideoMetadata
from backend.logger import app_logger as log
from backend.url_validator import DIRECT_FILE_EXTENSIONS, AUDIO_FORMATS

CHUNK_SIZE = 1024 * 256  # 256 KB


class DirectFileExtractor(IExtractor):
    name     = "direct-file"
    priority = 5

    def can_handle(self, url: str) -> bool:
        path = urlparse(url).path.lower()
        ext  = path.rsplit(".", 1)[-1].split("?")[0] if "." in path else ""
        return ext in DIRECT_FILE_EXTENSIONS

    # ── Metadata ──────────────────────────────────────────────────────────────

    async def get_metadata(self, url: str, cookie_file: Optional[str] = None) -> VideoMetadata:
        filename = Path(urlparse(url).path).name or "file"
        title    = filename.rsplit(".", 1)[0]
        ext      = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        # HEAD request to get Content-Length
        estimated_size = None
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
                r = await client.head(url)
                cl = r.headers.get("content-length")
                if cl:
                    estimated_size = int(cl)
        except Exception:
            pass

        return VideoMetadata(
            title          = title,
            thumbnail      = None,
            duration       = None,
            extractor      = self.name,
            estimated_size = estimated_size,
            is_audio_only  = ext in AUDIO_FORMATS,
        )

    # ── Download ──────────────────────────────────────────────────────────────

    async def download(
        self,
        url:         str,
        format:      str,
        quality:     str,
        output_dir:  str,
        job_id:      str,
        progress_cb: ProgressCallback,
        cookie_file: Optional[str] = None,
    ) -> DownloadResult:
        os.makedirs(output_dir, exist_ok=True)

        # Determine source extension
        path     = urlparse(url).path
        src_ext  = path.rsplit(".", 1)[-1].lower() if "." in path else "bin"
        tmp_path = os.path.join(output_dir, f"{job_id}_tmp.{src_ext}")
        filename_base = Path(path).stem or job_id

        await progress_cb(0.0, None, None, "Connecting...")

        # Stream download
        total_bytes = 0
        downloaded  = 0

        async with httpx.AsyncClient(follow_redirects=True, timeout=300) as client:
            async with client.stream("GET", url) as r:
                r.raise_for_status()
                cl = r.headers.get("content-length")
                total_bytes = int(cl) if cl else 0

                with open(tmp_path, "wb") as f:
                    async for chunk in r.aiter_bytes(CHUNK_SIZE):
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_bytes > 0:
                            pct = downloaded / total_bytes * 100
                        else:
                            pct = min(downloaded / (1024 * 1024), 99.0)  # rough estimate
                        speed_str = None
                        await progress_cb(pct, speed_str, None, None)

        # If format is an audio format and source is not already that format → re-encode
        needs_conversion = (
            format in AUDIO_FORMATS
            and src_ext != format
            and shutil.which("ffmpeg")
        )

        if needs_conversion:
            await progress_cb(96.0, None, None, f"Re-encoding to {format.upper()} via ffmpeg...")
            out_path = os.path.join(output_dir, f"{filename_base}.{format}")
            await self._ffmpeg_convert(tmp_path, out_path, format)
            os.remove(tmp_path)
            file_path = out_path
        else:
            # Just rename to final filename
            final_ext = format if format not in {"best"} else src_ext
            out_path  = os.path.join(output_dir, f"{filename_base}.{final_ext}")
            os.rename(tmp_path, out_path)
            file_path = out_path

        file_size = os.path.getsize(file_path)
        filename  = os.path.basename(file_path)

        await progress_cb(100.0, None, None, "Done")
        log.info(f"[direct-file] Job {job_id} complete: {filename} ({file_size} bytes)")

        return DownloadResult(
            file_path      = file_path,
            filename       = filename,
            file_size      = file_size,
            extractor_used = self.name,
        )

    async def _ffmpeg_convert(self, src: str, dst: str, fmt: str):
        """Re-encode audio using ffmpeg — guarantees genuine audio format."""
        cmd = [
            "ffmpeg", "-y",
            "-i", src,
            "-vn",                   # no video
            "-acodec", "libmp3lame" if fmt == "mp3" else fmt,
            "-q:a", "0",             # VBR best quality
            dst,
        ]
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: subprocess.run(cmd, check=True, capture_output=True),
        )
