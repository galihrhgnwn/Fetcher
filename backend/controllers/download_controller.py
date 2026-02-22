"""
Download Controller — all HTTP route handlers.

Rate limiting is applied globally via slowapi middleware in main.py.
Individual route decorators are NOT used to avoid Pydantic body-param conflicts.
"""
from __future__ import annotations
import asyncio
import os
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse

from backend.models import (
    MetadataRequest, StartDownloadRequest,
    MetadataResponse, StartDownloadResponse,
    JobStatusResponse, ValidateUrlResponse,
    CancelResponse,
)
from backend.url_validator import validate_url
from backend.services.download_service import download_service
from backend.services.sse_service import sse_service
from backend.extractors.registry import registry
from backend.cookie_manager import list_available_cookies
from backend.logger import app_logger as log

router = APIRouter(prefix="/api", tags=["download"])

# MIME map — MP3 MUST be audio/mpeg, never video/mp4
MIME_MAP = {
    "mp4":  "video/mp4",
    "webm": "video/webm",
    "mkv":  "video/x-matroska",
    "avi":  "video/x-msvideo",
    "mov":  "video/quicktime",
    "mp3":  "audio/mpeg",        # ← THE FIX: never video/mp4
    "m4a":  "audio/mp4",
    "opus": "audio/ogg",
    "ogg":  "audio/ogg",
    "wav":  "audio/wav",
    "flac": "audio/flac",
    "aac":  "audio/aac",
    "zip":  "application/zip",
    "pdf":  "application/pdf",
}


@router.get("/health")
async def health():
    return {"status": "ok", "service": "Fetcher v3.0"}


@router.post("/validate", response_model=ValidateUrlResponse)
async def validate(body: MetadataRequest):
    r = validate_url(body.url)
    return ValidateUrlResponse(
        valid=r.valid,
        url_type=r.url_type,
        normalised=r.normalised,
        error=r.error,
    )


@router.post("/metadata", response_model=MetadataResponse)
async def get_metadata(body: MetadataRequest):
    val = validate_url(body.url)
    if not val.valid:
        raise HTTPException(status_code=422, detail=val.error)
    try:
        meta = await download_service.get_metadata(val.normalised)
    except Exception as e:
        log.error(f"Metadata error: {e}")
        raise HTTPException(status_code=502, detail=str(e))
    return MetadataResponse(metadata=meta, url_type=val.url_type)


@router.post("/download/start", response_model=StartDownloadResponse)
async def start_download(body: StartDownloadRequest):
    val = validate_url(body.url)
    if not val.valid:
        raise HTTPException(status_code=422, detail=val.error)
    job = download_service.start_download(
        url=val.normalised,
        format=body.format,
        quality=body.quality,
    )
    return StartDownloadResponse(job_id=job.id, status=job.status)


@router.get("/download/{job_id}/status", response_model=JobStatusResponse)
async def job_status(job_id: str):
    job = download_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return JobStatusResponse(
        id=job.id, url=job.url, format=job.format, quality=job.quality,
        status=job.status, progress=job.progress, speed=job.speed, eta=job.eta,
        filename=job.filename, file_size=job.file_size, error=job.error,
        created_at=job.created_at, updated_at=job.updated_at,
    )


@router.get("/download/{job_id}/progress")
async def progress_stream(job_id: str):
    """Server-Sent Events stream for real-time progress."""
    if not download_service.get_job(job_id):
        raise HTTPException(status_code=404, detail="Job not found.")

    queue = sse_service.subscribe(job_id)

    async def generator() -> AsyncGenerator[str, None]:
        try:
            while True:
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=30.0)
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
                    continue
                if payload is None:
                    yield "event: close\ndata: {}\n\n"
                    break
                yield f"data: {payload}\n\n"
        finally:
            sse_service.unsubscribe(job_id, queue)

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/download/{job_id}/file")
async def serve_file(job_id: str):
    """Serve the completed download file with correct Content-Type."""
    file_path = download_service.get_file_path(job_id)
    if not file_path:
        raise HTTPException(status_code=404, detail="File not ready or job not found.")

    job      = download_service.get_job(job_id)
    filename = job.filename if job and job.filename else os.path.basename(file_path)
    ext      = os.path.splitext(file_path)[1].lstrip(".").lower()

    # MP3 MUST be audio/mpeg — this is the critical fix
    media_type = MIME_MAP.get(ext, "application/octet-stream")

    log.info(f"Serving file: {filename} ({media_type})")
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/download/{job_id}/cancel", response_model=CancelResponse)
async def cancel_download(job_id: str):
    if not download_service.cancel_job(job_id):
        raise HTTPException(status_code=400, detail="Job cannot be cancelled.")
    return CancelResponse(success=True, message="Download cancelled.")


@router.get("/history")
async def get_history():
    return [
        {
            "id": h.id, "url": h.url, "title": h.title, "format": h.format,
            "file_size": h.file_size, "thumbnail": h.thumbnail,
            "downloaded_at": h.downloaded_at,
        }
        for h in download_service.get_history()
    ]


@router.get("/extractors")
async def list_extractors():
    return registry.list_extractors()


@router.get("/cookies")
async def list_cookies():
    return list_available_cookies()
