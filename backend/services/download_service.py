"""
Download Service — orchestrates metadata fetching, download, conversion, and SSE events.
"""
from __future__ import annotations
import asyncio
import os
import uuid
import time
from typing import Optional

from backend.models import JobStatus, VideoMetadata, SSEEvent
from backend.services.job_store import job_store, Job, HistoryEntry
from backend.services.sse_service import sse_service
from backend.extractors.registry import registry
from backend.cookie_manager import get_cookie_file
from backend.url_validator import validate_url, _classify
from backend.logger import app_logger as log

DOWNLOAD_DIR = os.environ.get("FETCHER_DOWNLOAD_DIR", "/tmp/fetcher-downloads")


class DownloadService:

    # ── Metadata ──────────────────────────────────────────────────────────────

    async def get_metadata(self, url: str) -> VideoMetadata:
        url_type    = _classify(url)
        cookie_file = get_cookie_file(url_type)
        extractor   = registry.resolve(url)
        log.info(f"[Service] Metadata via {extractor.name} for {url[:60]}")
        return await extractor.get_metadata(url, cookie_file=cookie_file)

    # ── Start Download ─────────────────────────────────────────────────────────

    def start_download(self, url: str, format: str, quality: str) -> Job:
        job_id = str(uuid.uuid4())
        job    = Job(id=job_id, url=url, format=format, quality=quality)
        job_store.create(job)
        # Fire-and-forget async task
        asyncio.create_task(self._run(job_id))
        return job

    async def _run(self, job_id: str):
        job = job_store.get(job_id)
        if not job:
            return

        url_type    = _classify(job.url)
        cookie_file = get_cookie_file(url_type)

        async def progress_cb(pct: float, speed: Optional[str], eta: Optional[str], msg: Optional[str]):
            if job_store.get(job_id) and job_store.get(job_id).status == JobStatus.CANCELLED:
                raise asyncio.CancelledError("Job cancelled by user")
            job_store.update(job_id, progress=pct, speed=speed, eta=eta)
            await sse_service.broadcast(job_id, SSEEvent(
                status   = JobStatus.DOWNLOADING,
                progress = pct,
                speed    = speed,
                eta      = eta,
                message  = msg,
            ))

        try:
            # ── Phase 1: Fetch metadata ────────────────────────────────────
            job_store.update(job_id, status=JobStatus.FETCHING_METADATA)
            await sse_service.broadcast(job_id, SSEEvent(
                status=JobStatus.FETCHING_METADATA, progress=0.0, message="Fetching info..."
            ))

            extractor = registry.resolve(job.url)
            try:
                meta = await extractor.get_metadata(job.url, cookie_file=cookie_file)
                title = meta.title
            except Exception:
                title = job.url

            # ── Phase 2: Download ──────────────────────────────────────────
            job_store.update(job_id, status=JobStatus.DOWNLOADING)
            await sse_service.broadcast(job_id, SSEEvent(
                status=JobStatus.DOWNLOADING, progress=0.0, message="Starting download..."
            ))

            result = await extractor.download(
                url         = job.url,
                format      = job.format,
                quality     = job.quality,
                output_dir  = DOWNLOAD_DIR,
                job_id      = job_id,
                progress_cb = progress_cb,
                cookie_file = cookie_file,
            )

            # ── Phase 3: Done ──────────────────────────────────────────────
            job_store.update(
                job_id,
                status    = JobStatus.DONE,
                progress  = 100.0,
                filename  = result.filename,
                file_path = result.file_path,
                file_size = result.file_size,
            )
            await sse_service.broadcast(job_id, SSEEvent(
                status    = JobStatus.DONE,
                progress  = 100.0,
                filename  = result.filename,
                file_size = result.file_size,
                message   = "Download complete",
            ))

            # Add to history
            job_store.add_history(HistoryEntry(
                id        = job_id,
                url       = job.url,
                title     = title,
                format    = job.format,
                file_size = result.file_size,
            ))

        except asyncio.CancelledError:
            job_store.update(job_id, status=JobStatus.CANCELLED)
            await sse_service.broadcast(job_id, SSEEvent(
                status=JobStatus.CANCELLED, progress=0.0, message="Cancelled"
            ))
        except Exception as e:
            log.error(f"[Service] Job {job_id} failed: {e}")
            job_store.update(job_id, status=JobStatus.ERROR, error=str(e))
            await sse_service.broadcast(job_id, SSEEvent(
                status=JobStatus.ERROR, progress=0.0, error=str(e)
            ))
        finally:
            await sse_service.close(job_id)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def get_job(self, job_id: str) -> Optional[Job]:
        return job_store.get(job_id)

    def get_file_path(self, job_id: str) -> Optional[str]:
        job = job_store.get(job_id)
        if job and job.status == JobStatus.DONE and job.file_path:
            if os.path.exists(job.file_path):
                return job.file_path
        return None

    def cancel_job(self, job_id: str) -> bool:
        return job_store.cancel(job_id)

    def get_history(self) -> list[HistoryEntry]:
        return job_store.get_history()


download_service = DownloadService()
