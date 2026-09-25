import unittest
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from dom_hydrate.diff_engine import diff_ssr_csr
from dom_hydrate.formatters import export_html_report
from dom_hydrate.human_report import build_human_report

class TestDiffEngine(unittest.TestCase):
    def test_detection_of_client_side_noindex(self):
        ssr_html = "<html><head><title>Safe Page</title></head><body><h1>Hello</h1></body></html>"
        csr_html = "<html><head><title>Safe Page</title><meta name='robots' content='noindex, nofollow'></head><body><h1>Hello</h1></body></html>"
        
        diff = diff_ssr_csr(ssr_html, csr_html, "https://example.com")
        self.assertTrue(diff["robots_danger"])
        self.assertLess(diff["health_score"], 70)

    def test_detection_of_dropped_schema(self):
        ssr_html = """
        <html><head>
        <script type="application/ld+json">{"@context": "https://schema.org", "@type": "Product", "name": "Desk"}</script>
        </head><body>Content</body></html>
        """
        csr_html = "<html><head></head><body>Content Hydrated</body></html>"
        
        diff = diff_ssr_csr(ssr_html, csr_html, "https://example.com")
        self.assertIn("Product", diff["schemas"]["dropped_on_hydration"])
        self.assertEqual(diff["schemas"]["ssr_count"], 1)
        self.assertEqual(diff["schemas"]["csr_count"], 0)

    def test_detection_of_client_only_links(self):
        ssr_html = "<html><body><nav><a href='/about'>About</a></nav></body></html>"
        csr_html = "<html><body><nav><a href='/about'>About</a><a href='/pricing'>Pricing</a></nav></body></html>"
        
        diff = diff_ssr_csr(ssr_html, csr_html, "https://example.com")
        self.assertEqual(diff["links"]["csr_only_internal_total"], 1)
        self.assertIn("https://example.com/pricing", diff["links"]["csr_only_internal"])

    def test_detection_of_social_crawler_blindspot(self):
        ssr_html = "<html><head><title>Blog Post</title></head><body>Content</body></html>"
        csr_html = "<html><head><title>Blog Post</title><meta property='og:title' content='Dynamic Blog Post'><meta property='og:image' content='https://example.com/cover.jpg'></head><body>Content</body></html>"

        diff = diff_ssr_csr(ssr_html, csr_html, "https://example.com/post")
        self.assertTrue(diff["social_crawler_blindspot"])
        self.assertGreater(len(diff["social"]["diffs"]), 0)
        self.assertLessEqual(diff["health_score"], 90)

    def test_human_report_explains_noindex_risk(self):
        ssr_html = "<html><head><title>Safe Page</title></head><body>Content</body></html>"
        csr_html = "<html><head><title>Safe Page</title><meta name='robots' content='noindex'></head><body>Content</body></html>"
        report = build_human_report(diff_ssr_csr(ssr_html, csr_html, "https://example.com"))

        self.assertEqual(report["status"], "Critical")
        self.assertIn("index", report["summary"].lower())
        self.assertIn("Render the intended robots", report["findings"][0]["recommended_fix"])

    def test_html_report_contains_findings_and_technical_evidence(self):
        diff = diff_ssr_csr(
            "<html><head><title>Server title</title></head><body>Content</body></html>",
            "<html><head><title>Client title</title></head><body>Content</body></html>",
            "https://example.com",
        )
        report = export_html_report(diff, {"ttfb_ms": 20}, {"render_time_ms": 100})

        self.assertIn("Findings", report)
        self.assertIn("Technical evidence", report)
        self.assertIn("Client title", report)

    def test_fetch_ssr_mocked(self):
        from unittest.mock import patch, MagicMock
        from dom_hydrate.fetcher import fetch_ssr

        mock_resp = MagicMock()
        mock_resp.url = "https://example.com"
        mock_resp.status_code = 200
        mock_resp.text = "<html><body><h1>SSR</h1></body></html>"
        mock_resp.content = b"<html><body><h1>SSR</h1></body></html>"
        mock_resp.headers = {"content-type": "text/html", "server": "cloudflare"}
        mock_resp.elapsed.total_seconds.return_value = 0.05

        with patch("requests.get", return_value=mock_resp):
            res = fetch_ssr("https://example.com")
            self.assertEqual(res["status_code"], 200)
            self.assertIn("<h1>SSR</h1>", res["html"])
            self.assertEqual(res["server"], "cloudflare")

    def test_render_csr_mocked(self):
        from unittest.mock import patch, MagicMock
        from dom_hydrate.renderer import render_csr

        mock_page = MagicMock()
        mock_page.content.return_value = "<html><body><h1>CSR Hydrated</h1></body></html>"

        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page

        mock_browser = MagicMock()
        mock_browser.new_context.return_value = mock_context

        mock_playwright = MagicMock()
        mock_playwright.chromium.launch.return_value = mock_browser

        mock_cm = MagicMock()
        mock_cm.__enter__.return_value = mock_playwright
        mock_cm.__exit__.return_value = None

        with patch("playwright.sync_api.sync_playwright", return_value=mock_cm):
            res = render_csr("https://example.com", wait_ms=0)
            self.assertIn("<h1>CSR Hydrated</h1>", res["html"])
            self.assertEqual(res["browser_bin"], "Playwright Chromium (Headless)")


if __name__ == "__main__":
    unittest.main()
