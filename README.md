# Fetcher v3.0 — Universal Media Downloader

**Python (FastAPI) backend + React (Vite + Tailwind) frontend**  
Download from YouTube, TikTok, Instagram, Twitter/X, SoundCloud, and 1000+ sites.

---

## Quick Start

### Prerequisites

```bash
# Python 3.9+
python3 --version

# Node.js + pnpm (for frontend build — one-time setup)
node --version
npm install -g pnpm   # or: curl -fsSL https://get.pnpm.io/install.sh | sh

# ffmpeg (REQUIRED for MP3 conversion)
sudo apt install ffmpeg          # Ubuntu/Debian
brew install ffmpeg              # macOS
# Windows: https://ffmpeg.org/download.html → add to PATH
```

### Install & Run

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Build frontend + start server (first time)
python run.py --build

# 3. Next time, just start the server
python run.py

# Open: http://localhost:8000
# API docs: http://localhost:8000/api/docs
```

### Development Mode (hot-reload)

```bash
# Terminal 1 — Python backend (auto-reload)
python run.py

# Terminal 2 — React frontend (Vite HMR)
cd frontend && pnpm dev
# Open: http://localhost:5173 (proxies /api → :8000)
```

---

## Project Structure

```
fetcher/
├── run.py                          # ← Start here: python run.py
├── requirements.txt                # pip install -r requirements.txt
├── .env.example                    # Copy to .env for custom config
├── .gitignore
├── README.md
│
├── cookies/                        # ← Place cookie files here
│   ├── README.md                   # Instructions for adding cookies
│   ├── tiktok.txt                  # (example — add your own)
│   ├── instagram.txt
│   └── youtube.txt
│
├── backend/                        # Python FastAPI backend
│   ├── main.py                     # FastAPI app + SPA serving
│   ├── models.py                   # Pydantic request/response models
│   ├── logger.py                   # Centralized loguru logger
│   ├── url_validator.py            # URL validation + platform detection
│   ├── cookie_manager.py           # Per-platform cookie file resolver
│   │
│   ├── extractors/                 # ── Plugin-based extractor system ──
│   │   ├── base.py                 # IExtractor abstract interface
│   │   ├── ytdlp_extractor.py      # yt-dlp plugin (1000+ sites)
│   │   ├── direct_file_extractor.py# Direct file plugin (.mp4/.mp3/etc.)
│   │   └── registry.py             # ExtractorRegistry (auto-detection)
│   │
│   ├── services/                   # ── Service layer ──
│   │   ├── job_store.py            # In-memory job store + history
│   │   ├── sse_service.py          # Server-Sent Events broadcaster
│   │   └── download_service.py     # Core orchestration
│   │
│   ├── controllers/                # ── HTTP layer ──
│   │   └── download_controller.py  # All API route handlers
│   │
│   └── middleware/
│       └── rate_limiter.py         # IP-based rate limiting (slowapi)
│
├── frontend/                       # React + Vite + Tailwind frontend
│   ├── src/
│   │   ├── App.tsx                 # Main app with all UI
│   │   ├── components/             # MetadataCard, FormatSelector, JobCard, etc.
│   │   ├── hooks/                  # useSSE, useClipboard
│   │   ├── store/useStore.ts       # Zustand global state
│   │   └── lib/api.ts              # API client + helpers
│   ├── dist/                       # Built output (served by FastAPI)
│   └── package.json
│
└── tests/                          # pytest unit tests (46 tests)
    ├── test_url_validator.py
    ├── test_registry.py
    └── test_job_store.py
```

---

## How the Modular Extractor System Works

### Plugin Contract (`backend/extractors/base.py`)

```python
class IExtractor(ABC):
    name:     str   # unique identifier
    priority: int   # higher = preferred when multiple match

    def can_handle(self, url: str) -> bool: ...
    async def get_metadata(self, url, cookie_file=None) -> VideoMetadata: ...
    async def download(self, url, format, quality, output_dir,
                       job_id, progress_cb, cookie_file=None) -> DownloadResult: ...
```

### Registry Auto-Detection

```python
registry = ExtractorRegistry()
registry.register(DirectFileExtractor())  # priority 5
registry.register(YtDlpExtractor())       # priority 10

# Auto-detect:
extractor = registry.resolve("https://youtube.com/watch?v=...")
# → YtDlpExtractor (priority 10, can_handle=True)

extractor = registry.resolve("https://cdn.example.com/video.mp4")
# → DirectFileExtractor (priority 5, can_handle=True for .mp4)
```

### Adding a Custom Extractor

```python
# backend/extractors/my_extractor.py
from backend.extractors.base import IExtractor, DownloadResult
from backend.models import VideoMetadata

class MyExtractor(IExtractor):
    name     = "my-extractor"
    priority = 15  # Higher than yt-dlp → wins when can_handle=True

    def can_handle(self, url: str) -> bool:
        return "mysite.com" in url

    async def get_metadata(self, url, cookie_file=None):
        return VideoMetadata(title="My Video", formats=[])

    async def download(self, url, format, quality, output_dir, job_id, progress_cb, cookie_file=None):
        # ... your download logic
        await progress_cb(100.0, None, None, "Done")
        return DownloadResult(file_path="/tmp/video.mp4", filename="video.mp4")
```

Register in `backend/extractors/registry.py`:
```python
from backend.extractors.my_extractor import MyExtractor
registry.register(MyExtractor())
```

---

## MP3 Conversion — The Fix

### The Bug (original code)
The original project downloaded MP4 and renamed the extension to `.mp3`.  
Result: invalid audio file, wrong `Content-Type: video/mp4`.

### The Fix (this version)

**yt-dlp postprocessor** (`ytdlp_extractor.py`):
```python
opts["format"] = "bestaudio/best"
opts["postprocessors"] = [{
    "key":              "FFmpegExtractAudio",
    "preferredcodec":   "mp3",    # genuine re-encode via LAME
    "preferredquality": "0",      # VBR best quality
}]
```

**Correct Content-Type** (`download_controller.py`):
```python
MIME_MAP = {
    "mp3": "audio/mpeg",   # ← THE FIX: never video/mp4
    "mp4": "video/mp4",
    ...
}
```

---

## Cookie Files

Place Netscape-format cookie files in `cookies/`:

```
cookies/
  tiktok.txt       ← TikTok session cookies
  instagram.txt    ← Instagram session cookies
  youtube.txt      ← YouTube (for age-restricted content)
  twitter.txt      ← Twitter/X
  ...
```

See `cookies/README.md` for detailed instructions on exporting cookies from your browser.

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET  | `/api/health` | Health check |
| POST | `/api/validate` | Validate + classify URL |
| POST | `/api/metadata` | Fetch metadata (title, thumbnail, duration) |
| POST | `/api/download/start` | Start download → returns `job_id` |
| GET  | `/api/download/{id}/status` | Poll job status |
| GET  | `/api/download/{id}/progress` | **SSE** real-time progress stream |
| GET  | `/api/download/{id}/file` | Download completed file |
| POST | `/api/download/{id}/cancel` | Cancel active job |
| GET  | `/api/history` | Recent downloads (in-memory) |
| GET  | `/api/extractors` | List registered plugins |
| GET  | `/api/cookies` | List active cookie files |
| GET  | `/api/docs` | Swagger UI |

---

## Running Tests

```bash
pip install pytest
python -m pytest tests/ -v
# 46 tests, all passing
```

---

## Configuration

Copy `.env.example` to `.env`:

```env
FETCHER_PORT=8000
FETCHER_HOST=0.0.0.0
FETCHER_DOWNLOAD_DIR=/tmp/fetcher-downloads
FETCHER_MAX_CONCURRENT=3
FETCHER_RATE_LIMIT=60
```

---

## Dependencies

```
fastapi        — async web framework
uvicorn        — ASGI server
yt-dlp         — multi-platform video extractor
httpx          — async HTTP client
pydantic       — data validation
slowapi        — rate limiting
loguru         — structured logging
ffmpeg         — audio/video conversion (system package)
```

Frontend: React 18 · Vite · Tailwind CSS · Radix UI · Zustand · Framer Motion
