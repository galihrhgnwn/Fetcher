"""
Fetcher v3.0 — FastAPI application entry point.

Serves:
  - /api/*         → REST API (download, metadata, SSE, etc.)
  - /*             → React SPA (built into frontend/dist/)
"""
from __future__ import annotations
import os
import time
from collections import defaultdict
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from backend.controllers.download_controller import router as download_router
from backend.logger import app_logger as log

# ── Create logs dir ───────────────────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)

# ── Simple in-process rate limiter middleware ─────────────────────────────────
_rate_store: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT   = int(os.environ.get("FETCHER_RATE_LIMIT", "60"))   # requests
RATE_WINDOW  = 60                                                  # seconds


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/api/") and request.url.path != "/api/health":
            ip  = request.client.host if request.client else "unknown"
            now = time.time()
            window_start = now - RATE_WINDOW
            hits = [t for t in _rate_store[ip] if t > window_start]
            if len(hits) >= RATE_LIMIT:
                return JSONResponse(
                    status_code=429,
                    content={"detail": f"Rate limit exceeded. Max {RATE_LIMIT} requests/minute."},
                )
            hits.append(now)
            _rate_store[ip] = hits
        return await call_next(request)


# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(
    title       = "Fetcher v3.0",
    description = "Universal media downloader — Python backend + React frontend",
    version     = "3.0.0",
    docs_url    = "/api/docs",
    redoc_url   = "/api/redoc",
    openapi_url = "/api/openapi.json",
)

# Middleware
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# ── API routes ────────────────────────────────────────────────────────────────
app.include_router(download_router)

# ── Global error handler ──────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_error_handler(request: Request, exc: Exception):
    log.error(f"Unhandled error on {request.url}: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})


# ── Serve React SPA ───────────────────────────────────────────────────────────
DIST_DIR = Path(__file__).parent.parent / "frontend" / "dist"

if DIST_DIR.exists():
    # Serve static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=str(DIST_DIR / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        """Serve index.html for all non-API routes (SPA client-side routing)."""
        index = DIST_DIR / "index.html"
        if index.exists():
            return FileResponse(str(index))
        return JSONResponse(
            status_code=503,
            content={"detail": "Frontend not built. Run: cd frontend && pnpm build"},
        )
else:
    @app.get("/")
    async def root():
        return JSONResponse(
            status_code=503,
            content={"detail": "Frontend not built. Run: cd frontend && pnpm build"},
        )
    log.warning("Frontend dist/ not found. Run 'cd frontend && pnpm build' first.")

log.info("Fetcher v3.0 started")
