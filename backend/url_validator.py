"""
URL Validator — validates, normalises, and classifies URLs.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

DIRECT_FILE_EXTENSIONS = {
    "mp4", "webm", "mkv", "avi", "mov", "flv", "wmv",
    "mp3", "m4a", "opus", "ogg", "wav", "flac", "aac",
    "zip", "rar", "7z", "tar", "gz",
    "pdf", "doc", "docx", "xls", "xlsx",
    "jpg", "jpeg", "png", "gif", "webp",
}

AUDIO_FORMATS = {"mp3", "m4a", "opus", "ogg", "wav", "flac", "aac"}

PLATFORM_PATTERNS: list[tuple[str, str]] = [
    (r"(?:youtube\.com/(?:watch|shorts|live|embed)|youtu\.be/)", "youtube"),
    (r"tiktok\.com/",                                             "tiktok"),
    (r"instagram\.com/",                                          "instagram"),
    (r"(?:twitter\.com|x\.com)/",                                "twitter"),
    (r"facebook\.com/",                                           "facebook"),
    (r"vimeo\.com/",                                              "vimeo"),
    (r"twitch\.tv/",                                              "twitch"),
    (r"soundcloud\.com/",                                         "soundcloud"),
    (r"reddit\.com/",                                             "reddit"),
    (r"dailymotion\.com/",                                        "dailymotion"),
    (r"bilibili\.com/",                                           "bilibili"),
    (r"rumble\.com/",                                             "rumble"),
    (r"odysee\.com/",                                             "odysee"),
    (r"bandcamp\.com/",                                           "bandcamp"),
    (r"nicovideo\.jp/",                                           "nicovideo"),
    (r"weibo\.com/",                                              "weibo"),
]

PRIVATE_IP_PATTERNS = [
    re.compile(r"^localhost$", re.I),
    re.compile(r"^127\.\d+\.\d+\.\d+$"),
    re.compile(r"^10\.\d+\.\d+\.\d+$"),
    re.compile(r"^192\.168\.\d+\.\d+$"),
    re.compile(r"^172\.(1[6-9]|2\d|3[01])\.\d+\.\d+$"),
    re.compile(r"^::1$"),
    re.compile(r"^0\.0\.0\.0$"),
]


@dataclass
class ValidationResult:
    valid: bool
    url_type: Optional[str] = None
    normalised: Optional[str] = None
    error: Optional[str] = None


def validate_url(raw: str) -> ValidationResult:
    url = raw.strip()
    if not url:
        return ValidationResult(valid=False, error="URL cannot be empty.")

    # Auto-prepend https:// if missing
    if not url.startswith(("http://", "https://")):
        if url.startswith("ftp://") or url.startswith("file://"):
            return ValidationResult(valid=False, error="Only HTTP/HTTPS URLs are supported.")
        url = "https://" + url

    try:
        parsed = urlparse(url)
    except Exception:
        return ValidationResult(valid=False, error="Invalid URL format.")

    if parsed.scheme not in ("http", "https"):
        return ValidationResult(valid=False, error="Only HTTP/HTTPS URLs are supported.")

    hostname = parsed.hostname or ""
    for pattern in PRIVATE_IP_PATTERNS:
        if pattern.match(hostname):
            return ValidationResult(valid=False, error="Private/loopback addresses are not allowed.")

    if not parsed.netloc:
        return ValidationResult(valid=False, error="URL must include a valid domain.")

    url_type = _classify(url)
    return ValidationResult(valid=True, url_type=url_type, normalised=url)


def _classify(url: str) -> str:
    lower = url.lower()
    for pattern, platform in PLATFORM_PATTERNS:
        if re.search(pattern, lower):
            return platform
    # Check for direct file by extension
    path = urlparse(url).path.lower()
    ext = path.rsplit(".", 1)[-1].split("?")[0] if "." in path else ""
    if ext in DIRECT_FILE_EXTENSIONS:
        return "direct_file"
    return "generic_web"


def is_audio_format(fmt: str) -> bool:
    return fmt.lower() in AUDIO_FORMATS
