"""
Headless Client-Side Rendering (CSR) hydrator.
Executes client-side JavaScript in headless Chromium and captures the hydrated DOM.
"""

import time
from typing import Dict, Any


def render_csr(url: str, wait_ms: int = 4000, timeout_sec: int = 30) -> Dict[str, Any]:
    """Render CSR hydration for target URL using headless Playwright Chromium."""
    start = time.perf_counter()
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ]
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800}
            )
            page = context.new_page()

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=timeout_sec * 1000)
            except Exception:
                # If network or wait condition times out, proceed with current DOM state
                pass

            if wait_ms > 0:
                page.wait_for_timeout(wait_ms)

            dom_html = page.content()
            browser.close()

            render_time_ms = round((time.perf_counter() - start) * 1000, 1)
            content_length = len(dom_html.encode("utf-8"))

            return {
                "url": url,
                "html": dom_html,
                "dom_html": dom_html,
                "render_time_ms": render_time_ms,
                "virtual_time_budget_ms": wait_ms,
                "content_length_bytes": content_length,
                "browser_bin": "Playwright Chromium (Headless)"
            }
    except ImportError:
        raise RuntimeError(
            "Playwright is required for headless CSR rendering. Install via: pip install playwright && playwright install chromium"
        )
    except Exception as e:
        raise RuntimeError(f"Headless browser hydration failed for {url}: {e}")
