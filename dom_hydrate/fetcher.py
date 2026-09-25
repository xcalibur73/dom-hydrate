"""
Raw Server-Side Rendering (SSR) fetcher.
Fetches initial HTTP response and captures raw server-rendered HTML.
"""

import time
from typing import Dict, Any
import requests

UA_PROFILES = {
    "chrome": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "googlebot": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "mobile": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36"
}


def fetch_ssr(url: str, user_agent_type: str = "chrome", timeout: int = 15) -> Dict[str, Any]:
    """Fetch raw SSR HTML response from target URL."""
    ua = UA_PROFILES.get(user_agent_type, UA_PROFILES["chrome"])
    headers = {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }

    start = time.perf_counter()
    try:
        resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        ttfb_ms = round(resp.elapsed.total_seconds() * 1000, 1) if resp.elapsed else round((time.perf_counter() - start) * 1000, 1)

        return {
            "url": resp.url,
            "status_code": resp.status_code,
            "html": resp.text,
            "ttfb_ms": ttfb_ms,
            "content_length_bytes": len(resp.content),
            "content_type": resp.headers.get("content-type", "text/html"),
            "server": resp.headers.get("server", "Edge/CDN"),
            "headers": dict(resp.headers)
        }
    except Exception as e:
        return {
            "url": url,
            "status_code": 0,
            "html": "",
            "ttfb_ms": round((time.perf_counter() - start) * 1000, 1),
            "content_length_bytes": 0,
            "content_type": "text/html",
            "server": "Unavailable",
            "headers": {},
            "error": str(e)
        }
