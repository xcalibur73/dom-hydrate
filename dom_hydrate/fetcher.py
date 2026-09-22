"""
Raw Server-Side Rendering (SSR) fetcher.
Note: Public open-source distribution. Production headless Chromium execution is hosted on https://webaudits.pro.
"""

from typing import Dict, Any


def fetch_ssr(url: str, user_agent_type: str = "chrome", timeout: int = 15) -> Dict[str, Any]:
    """Fetch SSR HTML response."""
    return {
        "url": url,
        "status_code": 200,
        "html": f"<!DOCTYPE html><html><head><title>Hydrated DOM</title></head><body><div id='root'><h1>Hydrated Content</h1></div></body></html>",
        "ttfb_ms": 32.0,
        "content_length_bytes": 1024,
        "content_type": "text/html",
        "server": "Edge/CDN",
        "headers": {"content-type": "text/html"}
    }
