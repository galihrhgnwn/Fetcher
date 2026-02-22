"""
yt-dlp Extractor — handles YouTube, TikTok, Instagram, Twitter/X, and 1000+ sites.

MP3 Fix:
  Uses FFmpegExtractAudio postprocessor with preferredcodec="mp3" and preferredquality="0".
  This forces yt-dlp to call ffmpeg and genuinely re-encode the audio stream using the
  LAME encoder — NOT just rename the file extension.
"""
from __future__ import annotations
import asyncio
import os
import re
import time
from pathlib import Path
from typing import Optional

import yt_dlp

from backend.extractors.base import IExtractor, DownloadResult, ProgressCallback
from backend.models import VideoMetadata, FormatOption
from backend.logger import app_logger as log

# Platforms that yt-dlp handles (not direct file links)
YTDLP_PLATFORMS = {
    "youtube", "tiktok", "instagram", "twitter", "facebook",
    "vimeo", "twitch", "soundcloud", "reddit", "dailymotion",
    "bilibili", "rumble", "odysee", "bandcamp", "nicovideo",
    "weibo", "generic_web",
}

QUALITY_FORMAT_MAP = {
    "best":   "bestvideo+bestaudio/best",
    "4320p":  "bestvideo[height<=4320]+bestaudio/best[height<=4320]",
    "2160p":  "bestvideo[height<=2160]+bestaudio/best[height<=2160]",
    "1440p":  "bestvideo[height<=1440]+bestaudio/best[height<=1440]",
    "1080p":  "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
    "720p":   "bestvideo[height<=720]+bestaudio/best[height<=720]",
    "480p":   "bestvideo[height<=480]+bestaudio/best[height<=480]",
    "360p":   "bestvideo[height<=360]+bestaudio/best[height<=360]",
    "240p":   "bestvideo[height<=240]+bestaudio/best[height<=240]",
    "144p":   "bestvideo[height<=144]+bestaudio/best[height<=144]",
}


class YtDlpExtractor(IExtractor):
    name     = "yt-dlp"
    priority = 10

    def can_handle(self, url: str) -> bool:
        from backend.url_validator import _classify
        url_type = _classify(url)
        return url_type in YTDLP_PLATFORMS

    # ── Metadata ──────────────────────────────────────────────────────────────

    async def get_metadata(self, url: str, cookie_file: Optional[str] = None) -> VideoMetadata:
        opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "extract_flat": False,
        }
        if cookie_file:
            opts["cookiefile"] = cookie_file

        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, lambda: self._extract_info(url, opts))

        formats = []
        for f in info.get("formats", []):
            formats.append(FormatOption(
                format_id  = f.get("format_id", ""),
                ext        = f.get("ext", ""),
                quality    = f.get("format_note", ""),
                resolution = f.get("resolution", ""),
                filesize   = f.get("filesize") or f.get("filesize_approx"),
                vcodec     = f.get("vcodec"),
                acodec     = f.get("acodec"),
                note       = f.get("format_note"),
            ))

        # Estimate size from best format
        estimated = None
        for f in reversed(info.get("formats", [])):
            s = f.get("filesize") or f.get("filesize_approx")
            if s:
                estimated = s
                break

        is_audio_only = info.get("vcodec") == "none" or not any(
            f.get("vcodec") and f.get("vcodec") != "none"
            for f in info.get("formats", [])
        )

        return VideoMetadata(
            title          = info.get("title", "Unknown"),
            thumbnail      = info.get("thumbnail"),
            duration       = info.get("duration"),
            uploader       = info.get("uploader") or info.get("channel"),
            upload_date    = info.get("upload_date"),
            view_count     = info.get("view_count"),
            description    = (info.get("description") or "")[:500],
            formats        = formats[:20],
            estimated_size = estimated,
            is_audio_only  = is_audio_only,
            extractor      = info.get("extractor_key", self.name),
        )

    def _extract_info(self, url: str, opts: dict):
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=False)

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
        outtmpl = os.path.join(output_dir, f"{job_id}.%(ext)s")

        is_audio = format in {"mp3", "m4a", "opus", "flac", "wav", "aac"}

        opts: dict = {
            "outtmpl":    outtmpl,
            "quiet":      True,
            "no_warnings": True,
            "progress_hooks": [self._make_progress_hook(progress_cb)],
            "noprogress": False,
        }

        if cookie_file:
            opts["cookiefile"] = cookie_file

        if is_audio:
            # ── MP3 FIX: genuine ffmpeg re-encode, NOT a rename ──────────────
            opts["format"] = "bestaudio/best"
            opts["postprocessors"] = [{
                "key":              "FFmpegExtractAudio",
                "preferredcodec":   format,          # "mp3", "m4a", etc.
                "preferredquality": "0",             # VBR best quality
            }]
        else:
            fmt_str = QUALITY_FORMAT_MAP.get(quality, QUALITY_FORMAT_MAP["best"])
            if format == "webm":
                fmt_str = fmt_str.replace("bestvideo", "bestvideo[ext=webm]")
            opts["format"] = fmt_str
            if format != "best":
                opts["merge_output_format"] = format

        await progress_cb(0.0, None, None, "Starting download...")

        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, lambda: self._run_download(url, opts))

        # Find the output file
        file_path = self._find_output_file(output_dir, job_id)
        if not file_path:
            raise FileNotFoundError(f"Output file not found after download for job {job_id}")

        filename  = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)

        await progress_cb(100.0, None, None, "Done")
        log.info(f"[yt-dlp] Job {job_id} complete: {filename} ({file_size} bytes)")

        return DownloadResult(
            file_path      = file_path,
            filename       = filename,
            file_size      = file_size,
            extractor_used = self.name,
        )

    def _run_download(self, url: str, opts: dict) -> dict:
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=True)

    def _find_output_file(self, output_dir: str, job_id: str) -> Optional[str]:
        """Find the file that starts with job_id in output_dir."""
        for f in Path(output_dir).iterdir():
            if f.name.startswith(job_id) and f.is_file():
                return str(f)
        return None

    def _make_progress_hook(self, progress_cb: ProgressCallback):
        """Create a yt-dlp progress hook that calls our async callback."""
        loop = asyncio.new_event_loop()

        def hook(d: dict):
            status = d.get("status")
            if status == "downloading":
                total     = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded = d.get("downloaded_bytes", 0)
                pct       = (downloaded / total * 100) if total > 0 else 0.0
                speed     = d.get("_speed_str", "").strip()
                eta       = d.get("_eta_str", "").strip()
                # Schedule the coroutine on the main event loop
                try:
                    asyncio.get_event_loop().call_soon_threadsafe(
                        lambda: asyncio.ensure_future(
                            progress_cb(pct, speed or None, eta or None, None)
                        )
                    )
                except Exception:
                    pass
            elif status == "finished":
                try:
                    asyncio.get_event_loop().call_soon_threadsafe(
                        lambda: asyncio.ensure_future(
                            progress_cb(95.0, None, None, "Converting...")
                        )
                    )
                except Exception:
                    pass

        return hook
