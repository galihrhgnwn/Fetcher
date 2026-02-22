#!/usr/bin/env python3
"""
Fetcher v3.0 — Launcher

Usage:
    python run.py                  # dev mode, port 8000, auto-reload
    python run.py --port 9000      # custom port
    python run.py --prod           # production mode (no reload)
    python run.py --build          # build frontend then start server
"""
import argparse
import subprocess
import sys
import os
from pathlib import Path

ROOT = Path(__file__).parent


def build_frontend():
    frontend = ROOT / "frontend"
    print("📦 Building frontend...")
    result = subprocess.run(["pnpm", "install"], cwd=frontend)
    if result.returncode != 0:
        print("❌ pnpm install failed")
        sys.exit(1)
    result = subprocess.run(["pnpm", "build"], cwd=frontend)
    if result.returncode != 0:
        print("❌ pnpm build failed")
        sys.exit(1)
    print("✅ Frontend built successfully")


def main():
    parser = argparse.ArgumentParser(description="Fetcher v3.0 server")
    parser.add_argument("--port",  type=int, default=int(os.environ.get("FETCHER_PORT", 8000)))
    parser.add_argument("--host",  default="0.0.0.0")
    parser.add_argument("--prod",  action="store_true", help="Production mode (no auto-reload)")
    parser.add_argument("--build", action="store_true", help="Build frontend before starting")
    args = parser.parse_args()

    if args.build:
        build_frontend()

    dist = ROOT / "frontend" / "dist"
    if not dist.exists():
        print("⚠️  Frontend not built. Run with --build flag or: cd frontend && pnpm build")

    cmd = [
        sys.executable, "-m", "uvicorn",
        "backend.main:app",
        "--host", args.host,
        "--port", str(args.port),
    ]
    if not args.prod:
        cmd.append("--reload")

    mode = "production" if args.prod else "development"
    print(f"\n🚀 Fetcher v3.0 starting in {mode} mode")
    print(f"   URL: http://localhost:{args.port}")
    print(f"   API: http://localhost:{args.port}/api/docs\n")

    os.execvp(sys.executable, cmd)


if __name__ == "__main__":
    main()
