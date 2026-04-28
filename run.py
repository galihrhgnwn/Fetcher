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
import shutil
import tarfile
import platform
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
NODE_ENV_DIR = ROOT / ".node_env"
NODE_DIR = ROOT / ".node_local"
NODE_VERSION = "20.14.0"


def run_cmd(cmd, **kwargs):
    return subprocess.run(cmd, **kwargs)


def is_available(cmd):
    return run_cmd(["which", cmd], capture_output=True).returncode == 0


def download_node():
    """Download Node.js binary tarball directly — no root needed."""
    machine = platform.machine().lower()
    arch = "arm64" if ("aarch64" in machine or "arm64" in machine) else "x64"
    url = f"https://nodejs.org/dist/v{NODE_VERSION}/node-v{NODE_VERSION}-linux-{arch}.tar.gz"
    dest = ROOT / f"node-v{NODE_VERSION}-linux-{arch}.tar.gz"

    print(f"⬇️  Downloading Node.js v{NODE_VERSION} ({arch})...")
    try:
        urllib.request.urlretrieve(url, dest)
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return None

    print("📂 Extracting Node.js...")
    with tarfile.open(dest, "r:gz") as tar:
        tar.extractall(ROOT)
    dest.unlink()

    node_extracted = ROOT / f"node-v{NODE_VERSION}-linux-{arch}"
    if NODE_DIR.exists():
        shutil.rmtree(NODE_DIR)
    node_extracted.rename(NODE_DIR)
    print("✅ Node.js downloaded successfully")
    return NODE_DIR / "bin"


def ensure_node_env():
    """
    Ensure Node.js + pnpm are available.
    Returns bin directory path, or None if system pnpm is used.
    """
    # 1. pnpm already available globally
    if is_available("pnpm"):
        return None

    # 2. nodeenv already set up
    if (NODE_ENV_DIR / "bin" / "pnpm").exists():
        print("✅ Using local nodeenv environment")
        return NODE_ENV_DIR / "bin"

    # 3. Node downloaded manually and pnpm installed
    if (NODE_DIR / "bin" / "pnpm").exists():
        print("✅ Using downloaded Node.js")
        return NODE_DIR / "bin"

    print("⚙️  Node.js/pnpm not found — bootstrapping...")

    # Cleanup any broken previous attempts
    for d in [NODE_ENV_DIR, NODE_DIR]:
        if d.exists():
            print(f"🧹 Cleaning up broken env: {d.name}")
            shutil.rmtree(d)

    bin_dir = None

    # Strategy 1: nodeenv --prebuilt
    run_cmd([sys.executable, "-m", "pip", "install", "nodeenv", "-q"])
    print("⚙️  Trying nodeenv --prebuilt...")
    result = run_cmd([sys.executable, "-m", "nodeenv", str(NODE_ENV_DIR), "--prebuilt"])
    if result.returncode == 0:
        bin_dir = NODE_ENV_DIR / "bin"

    # Strategy 2: nodeenv --node=system
    if bin_dir is None:
        print("⚠️  Prebuilt failed, trying --node=system...")
        if NODE_ENV_DIR.exists():
            shutil.rmtree(NODE_ENV_DIR)
        result = run_cmd([sys.executable, "-m", "nodeenv", str(NODE_ENV_DIR), "--node=system"])
        if result.returncode == 0:
            bin_dir = NODE_ENV_DIR / "bin"

    # Strategy 3: download Node.js tarball directly
    if bin_dir is None:
        print("⚠️  nodeenv failed, downloading Node.js directly (no root needed)...")
        if NODE_ENV_DIR.exists():
            shutil.rmtree(NODE_ENV_DIR)
        bin_dir = download_node()

    if bin_dir is None:
        print("❌ All strategies failed. Please install Node.js manually.")
        sys.exit(1)

    # Install pnpm with PATH pointing to our node bin
    node_env = {
        **os.environ,
        "PATH": str(bin_dir) + os.pathsep + os.environ.get("PATH", ""),
    }
    npm_bin = bin_dir / "npm"
    print("⚙️  Installing pnpm...")
    result = run_cmd([str(npm_bin), "install", "-g", "pnpm"], env=node_env)
    if result.returncode != 0:
        print("❌ pnpm install failed.")
        sys.exit(1)

    print("✅ Node.js + pnpm ready")
    return bin_dir


def build_frontend():
    frontend = ROOT / "frontend"
    bin_dir = ensure_node_env()

    if bin_dir:
        pnpm = str(bin_dir / "pnpm")
        env = {**os.environ, "PATH": str(bin_dir) + os.pathsep + os.environ.get("PATH", "")}
    else:
        pnpm = "pnpm"
        env = None

    print("📦 Building frontend...")

    result = run_cmd([pnpm, "install"], cwd=frontend, env=env)
    if result.returncode != 0:
        print("❌ pnpm install failed")
        sys.exit(1)

    result = run_cmd([pnpm, "build"], cwd=frontend, env=env)
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
