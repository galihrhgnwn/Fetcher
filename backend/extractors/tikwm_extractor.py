"""
TikWM Extractor — handles TikTok downloads without requiring cookies.
Uses the tikwm.com API.
"""
from __future__ import annotations
import asyncio
import os
import requests
from typing import Optional
from pathlib import Path

from backend.extractors.base import IExtractor, DownloadResult, ProgressCallback
from backend.models import VideoMetadata, FormatOption
from backend.logger import app_logger as log

class TikWMExtractor(IExtractor):
    name     = "tikwm"
    priority = 20  # Higher priority than yt-dlp for TikTok

    def can_handle(self, url: str) -> bool:
        from backend.url_validator import _classify
        url_type = _classify(url)
        return url_type == "tiktok"

    async def get_metadata(self, url: str, cookie_file: Optional[str] = None) -> VideoMetadata:
        # TikWM doesn't need cookies
        api_url = "https://www.tikwm.com/api/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        data = {"url": url, "hd": 1}
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: requests.post(api_url, data=data, headers=headers, timeout=10))
        
        if response.status_code != 200:
            raise Exception(f"TikWM API returned status code {response.status_code}")
            
        res_json = response.json()
        if res_json.get("code") != 0:
            raise Exception(f"TikWM API Error: {res_json.get('msg')}")
            
        video_data = res_json.get("data", {})
        
        # TikWM provides limited format options compared to yt-dlp
        # We'll expose the main 'play' and 'hdplay' as formats
        formats = []
        if video_data.get("play"):
            formats.append(FormatOption(
                format_id  = "standard",
                ext        = "mp4",
                quality    = "Standard",
                resolution = "SD",
                note       = "Standard quality (watermark-free)"
            ))
        if video_data.get("hdplay"):
            formats.append(FormatOption(
                format_id  = "hd",
                ext        = "mp4",
                quality    = "HD",
                resolution = "HD",
                note       = "High definition (watermark-free)"
            ))
        if video_data.get("music"):
            formats.append(FormatOption(
                format_id  = "audio",
                ext        = "mp3",
                quality    = "Audio",
                resolution = "Audio",
                note       = "Original audio"
            ))

        return VideoMetadata(
            title          = video_data.get("title", "TikTok Video"),
            thumbnail      = video_data.get("cover"),
            duration       = video_data.get("duration"),
            uploader       = video_data.get("author", {}).get("nickname"),
            upload_date    = None, # TikWM doesn't provide this clearly in the main data
            view_count     = video_data.get("play_count"),
            description    = video_data.get("title", ""),
            formats        = formats,
            estimated_size = None,
            is_audio_only  = False,
            extractor      = self.name,
        )

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
        # Re-fetch metadata to get the latest download links
        metadata = await self.get_metadata(url)
        
        # Decide which URL to use
        # If format is audio, use music URL
        # Otherwise use hdplay or play based on quality
        api_url = "https://www.tikwm.com/api/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        data = {"url": url, "hd": 1}
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: requests.post(api_url, data=data, headers=headers, timeout=10))
        video_data = response.json().get("data", {})
        
        download_url = ""
        if format in {"mp3", "m4a", "opus", "flac", "wav", "aac"}:
            download_url = video_data.get("music")
            final_ext = "mp3"
        else:
            if quality == "hd" and video_data.get("hdplay"):
                download_url = video_data.get("hdplay")
            else:
                download_url = video_data.get("play")
            final_ext = "mp4"

        if not download_url:
            raise Exception("Could not find a valid download URL from TikWM")
            
        if download_url.startswith('/'):
            download_url = f"https://www.tikwm.com{download_url}"

        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, f"{job_id}.{final_ext}")

        await progress_cb(10.0, None, None, "Starting download from TikWM...")
        
        # Perform the actual download
        def _download_file():
            with requests.get(download_url, stream=True, timeout=30) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                downloaded = 0
                with open(file_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                # We can't easily call the async progress_cb from here
                                # but we'll just finish and report 100%
                                pass
            return os.path.getsize(file_path)

        file_size = await loop.run_in_executor(None, _download_file)
        
        await progress_cb(100.0, None, None, "Done")
        
        return DownloadResult(
            file_path      = file_path,
            filename       = os.path.basename(file_path),
            file_size      = file_size,
            extractor_used = self.name,
        )
