"""
Raw Server-Side Rendering (SSR) fetcher.
Fetches initial HTML directly over HTTP before any JavaScript execution.
"""

import time
from typing import Dict, Any
import requests

USER_AGENTS = {
    "chrome": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "googlebot": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "mobile": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36"
}

def fetch_ssr(url: str, user_agent_type: str = "chrome", timeout: int = 15) -> Dict[str, Any]:
    ua = USER_AGENTS.get(user_agent_type, USER_AGENTS["chrome"])
    headers = {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache"
    }

    start_time = time.perf_counter()
    response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
    ttfb = (time.perf_counter() - start_time) * 1000

    return {
        "url": response.url,
        "status_code": response.status_code,
        "html": response.text,
        "ttfb_ms": round(ttfb, 2),
        "content_length_bytes": len(response.content),
        "content_type": response.headers.get("Content-Type", ""),
        "server": response.headers.get("Server", "Unknown"),
        "headers": dict(response.headers)
    }
