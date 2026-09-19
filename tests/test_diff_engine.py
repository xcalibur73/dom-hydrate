import unittest
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from dom_hydrate.diff_engine import diff_ssr_csr

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


if __name__ == "__main__":
    unittest.main()
