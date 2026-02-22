"""
Cookie Manager — resolves per-platform Netscape-format cookie files.

Cookie files live in the `cookies/` directory at the project root:
  cookies/
    youtube.txt
    tiktok.txt
    instagram.txt
    twitter.txt
    facebook.txt
    ...

yt-dlp accepts these via the --cookies flag.
"""
from __future__ import annotations
import os
from pathlib import Path
from typing import Optional
from backend.logger import app_logger as log

# Root of the project (two levels up from this file)
PROJECT_ROOT = Path(__file__).parent.parent
COOKIES_DIR  = PROJECT_ROOT / "cookies"

# Map of platform name → possible cookie filenames (first match wins)
PLATFORM_COOKIE_FILES: dict[str, list[str]] = {
    "youtube":     ["youtube.txt", "youtube.com.txt"],
    "tiktok":      ["tiktok.txt", "tiktok.com.txt"],
    "instagram":   ["instagram.txt", "instagram.com.txt"],
    "twitter":     ["twitter.txt", "x.txt", "twitter.com.txt"],
    "facebook":    ["facebook.txt", "facebook.com.txt"],
    "vimeo":       ["vimeo.txt", "vimeo.com.txt"],
    "twitch":      ["twitch.txt", "twitch.tv.txt"],
    "soundcloud":  ["soundcloud.txt", "soundcloud.com.txt"],
    "reddit":      ["reddit.txt", "reddit.com.txt"],
    "dailymotion": ["dailymotion.txt", "dailymotion.com.txt"],
    "bilibili":    ["bilibili.txt", "bilibili.com.txt"],
    "nicovideo":   ["nicovideo.txt", "nicovideo.jp.txt"],
    "weibo":       ["weibo.txt", "weibo.com.txt"],
    "rumble":      ["rumble.txt", "rumble.com.txt"],
    "odysee":      ["odysee.txt", "odysee.com.txt"],
    "bandcamp":    ["bandcamp.txt", "bandcamp.com.txt"],
}


def get_cookie_file(platform: str) -> Optional[str]:
    """
    Return the absolute path to the cookie file for the given platform,
    or None if no cookie file exists.
    """
    if not COOKIES_DIR.exists():
        return None

    candidates = PLATFORM_COOKIE_FILES.get(platform.lower(), [f"{platform}.txt"])
    for filename in candidates:
        path = COOKIES_DIR / filename
        if path.exists() and path.stat().st_size > 0:
            log.debug(f"[Cookies] Using {path} for platform '{platform}'")
            return str(path)

    # Fallback: try generic cookies.txt
    generic = COOKIES_DIR / "cookies.txt"
    if generic.exists() and generic.stat().st_size > 0:
        log.debug(f"[Cookies] Using generic cookies.txt for platform '{platform}'")
        return str(generic)

    return None


def list_available_cookies() -> list[dict]:
    """Return a list of available cookie files with their platform associations."""
    if not COOKIES_DIR.exists():
        return []

    result = []
    for path in sorted(COOKIES_DIR.glob("*.txt")):
        if path.stat().st_size > 0:
            # Guess platform from filename
            stem = path.stem.lower().replace(".com", "").replace(".tv", "")
            result.append({
                "file": path.name,
                "platform": stem,
                "size": path.stat().st_size,
            })
    return result
