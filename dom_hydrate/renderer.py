"""
Headless Client-Side Rendering (CSR) hydrator.
Uses native Chromium/Chrome/Edge executable with --headless=new --dump-dom.
"""

import os
import shutil
import subprocess
import time
from typing import Dict, Any, Optional

CANDIDATE_BROWSER_PATHS = [
    # Windows
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    # macOS
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    # Linux
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser"
]

def find_browser_executable() -> Optional[str]:
    for path in CANDIDATE_BROWSER_PATHS:
        if os.path.isabs(path):
            if os.path.exists(path) and os.path.isfile(path):
                return path
        else:
            resolved = shutil.which(path)
            if resolved:
                return resolved
    return None

def render_csr(url: str, wait_ms: int = 4000, timeout_sec: int = 30) -> Dict[str, Any]:
    browser_bin = find_browser_executable()
    if not browser_bin:
        raise RuntimeError("No compatible Chromium or Chrome/Edge browser binary found on system.")

    args = [
        browser_bin,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--disable-extensions",
        "--disable-software-rasterizer",
        f"--virtual-time-budget={wait_ms}",
        "--dump-dom",
        url
    ]

    start_time = time.perf_counter()
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout_sec, encoding="utf-8", errors="replace")
        render_time_ms = (time.perf_counter() - start_time) * 1000
    except subprocess.TimeoutExpired:
        raise TimeoutError(f"Headless browser timed out after {timeout_sec}s rendering {url}")

    if proc.returncode != 0 and not proc.stdout:
        raise RuntimeError(f"Browser failed to dump DOM (exit code {proc.returncode}): {proc.stderr}")

    html = proc.stdout

    return {
        "html": html,
        "browser_path": browser_bin,
        "render_time_ms": round(render_time_ms, 2),
        "content_length_bytes": len(html.encode("utf-8")),
        "wait_budget_ms": wait_ms
    }
