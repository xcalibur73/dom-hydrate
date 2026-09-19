# DOMHydrate

Forensic CSR vs. SSR SEO diff engine with headless Chromium DOM dumping.

Part of the [WebAudits.pro](https://webaudits.pro) technical intelligence platform.

---

## What it does

DOMHydrate compares raw server-rendered HTML (SSR) against the fully hydrated browser Document Object Model (CSR) rendered by headless Chromium. It detects:
- Metadata and directive parity regressions (`<title>`, `<meta name="description">`, `<link rel="canonical">`, `<meta name="robots">`).
- Client-side injection of restrictive directives (such as `noindex` or `nofollow` added during hydration).
- Structured data drops (Schema.org JSON-LD scripts present in server HTML but removed or malformed client-side).
- Link graph expansion and mutation (internal links that appear or disappear after JavaScript execution).
- DOM tree inflation and node count expansion between initial payload and final layout.

---

## Why it exists

Modern JavaScript frameworks (Next.js, Nuxt, Remix, SvelteKit, Angular) deliver an initial server-rendered HTML string that client-side hydration then mounts and mutates. Search engine crawlers do not execute JavaScript uniformly:
- Googlebot executes JavaScript in a deferred secondary indexing wave when rendering resources become available.
- Other search engines (Bing, Yahoo, DuckDuckGo, regional engines) and AI retrieval bots (OAI-SearchBot, Claude-SearchBot, PerplexityBot) often index only the initial server response.

When critical SEO directives, canonical tags, or structured data exist only in client-hydrated markup (or get dropped by rogue client scripts), indexation mismatches occur. DOMHydrate isolates these discrepancies locally or in CI pipelines before deployment.

---

## Key features

- **Dual-State Capture:** Fetches initial server markup via raw HTTP request and renders hydrated DOM using native Chromium (`--headless=new --dump-dom`).
- **Configurable Hydration Buffer:** Configurable post-navigation rendering delay (default: 4,000ms) to ensure asynchronous data fetches and hydration cycles complete.
- **User-Agent Emulation:** Supports desktop Chrome, Googlebot desktop, and Googlebot smartphone crawler profiles.
- **Critical Danger Alert:** Immediate warning if client-side hydration injects a `noindex` tag onto an otherwise indexable page.
- **Multiple Output Formats:** Formatted terminal tables via Rich, machine-readable JSON for CI/CD gates, and Markdown summaries.

---

## Architecture

```text
[Target URL]
     |
     +---> [HTTP Fetcher] --------------> Raw SSR HTML --------+
     |                                                         |
     +---> [Headless Chromium (--dump-dom)] -> Hydrated CSR DOM +
                                                               |
                                                               v
                                                      [DOM Diff Engine]
                                                               |
                     +-----------------------------------------+-----------------------------------------+
                     |                                         |                                         |
                     v                                         v                                         v
            [Metadata & Directives]                   [Schema.org Blocks]                       [Link Graph & Nodes]
```

DOMHydrate operates in three stages:
1. `fetcher.py`: Performs an HTTP GET request with the specified crawler User-Agent, capturing raw server response body, TTFB, and headers.
2. `renderer.py`: Launches headless Chromium with `--headless=new`, disables GPU acceleration, waits for network idle, and extracts serialized DOM via `--dump-dom`.
3. `diff_engine.py`: Parses both trees using BeautifulSoup, normalizes whitespace and attributes, and computes categorical diffs across metadata, Schema.org entities, internal links, and DOM node counts.

---

## Installation

### Prerequisites
- Python 3.10 or higher
- Google Chrome or Chromium installed and available in system PATH

### Install from Source
```bash
git clone https://github.com/xcalibur73/dom-hydrate.git
cd dom-hydrate
pip install -r requirements.txt
pip install -e .
```

---

## Usage

### Basic CLI Invocation
```bash
# Audit a live URL
dom-hydrate https://webaudits.pro

# Emulate Googlebot smartphone crawler
dom-hydrate https://webaudits.pro --ua mobile

# Increase hydration wait buffer for heavy SPAs (6,000ms)
dom-hydrate https://example.com --wait 6000

# Export structured JSON for CI/CD pipeline
dom-hydrate https://example.com --output json --save audit.json

# Check installed version
dom-hydrate --version
```

---

## Example output

```text
+-------------------------------------------------------------------------------+
| DOMHydrate: CSR vs. SSR SEO Diff Engine                                       |
| Target: https://webaudits.pro                                                 |
| Hydration Health Score: 100.0/100                                             |
| SSR TTFB: 306ms | Browser Render Time: 1621ms                                 |
+-------------------------------------------------------------------------------+

Metadata & Directives Parity:
+-------------------+--------------------+--------------------+---------+
| Directive / Tag   | Raw Server (SSR)   | Hydrated (CSR)     | Status  |
+-------------------+--------------------+--------------------+---------+
| title             | WebAudits.pro -... | WebAudits.pro -... | PARITY  |
| meta_description  | Comprehensive w... | Comprehensive w... | PARITY  |
| canonical         | https://webaudi... | https://webaudi... | PARITY  |
| meta_robots       | index, follow      | index, follow      | PARITY  |
+-------------------+--------------------+--------------------+---------+

Structured Data (Schema.org JSON-LD):
- SSR Schemas Count: 2
- CSR Schemas Count: 2
- Dropped on Hydration: None
- Injected on Hydration: None

Link Graph & DOM Footprint:
- SSR Internal Links: 40 | CSR Internal Links: 40 (0 client-only)
- DOM Node Count: 726 (SSR) vs. 726 (CSR) -> 0.0% node bloat
```

---

## Benchmark / methodology

### Empirical 12-Site Benchmark Study
- **Dataset:** 12 production web properties across static, hybrid Next.js, and client-heavy single-page architectures (`webaudits.pro`, `nextjs.org`, `github.com`, `linear.app`, `theverge.com`, `shopify.com`, etc.).
- **Command Used:** `python run.py <url> --output json`
- **Tool Version:** DOMHydrate v1.0.0
- **Environment:** Windows 11, Chromium 128.0, Python 3.12, 1 Gbps fiber connection, 2026-09-19.
- **Raw Telemetry & Calculation:**
  - Node expansion percentage: `((CSR_nodes - SSR_nodes) / SSR_nodes) * 100`
  - Link parity ratio: `(CSR_internal_links_matching_SSR / SSR_internal_links) * 100`
- **Results:**
  - Static-first architectures (`webaudits.pro`, `python.org`) maintain 0.0% node expansion and 100% link parity.
  - Interactive single-page apps expand DOM trees by +13% to +30%, adding 380 to 720 additional nodes during hydration.
  - Complete empirical dataset: [BENCHMARKS.md](BENCHMARKS.md).

---

## Limitations

- **Diagnostic Heuristic:** The Hydration Health Score is a project-derived heuristic and does not guarantee Google indexing status.
- **Proprietary Renderer Differences:** Googlebot uses a specialized headless Chromium build with dynamic rendering quotas. DOMHydrate uses your local Chromium binary, which accurately reflects modern browser rendering but cannot predict Googlebot rendering timeouts on resource-starved servers.
- **Session State:** Does not simulate user authentication, localStorage states, or dynamic cookie consent banners unless pre-configured.

---

## Accuracy / standards

DOMHydrate categorizes its diagnostic metrics as follows:

| Metric | Classification | Authority / Standard |
|:---|:---|:---|
| Canonical URL Resolution | Google / Web Standard | RFC 6596 |
| Robots Directives (`noindex`) | Google / Web Standard | Google Search Central Specifications |
| Schema.org JSON-LD Extraction | Web Standard | W3C JSON-LD 1.1 Standard |
| DOM Node Expansion Rate | Project-Derived Heuristic | Empirical baseline (0% optimal, >25% risk) |
| Hydration Health Score | Project-Derived Heuristic | Weighted parity formula (100-point scale) |

---

## Testing

DOMHydrate includes unit tests covering diff calculation, metadata extraction, Schema.org parsing, and danger flag detection:

```bash
# Run unit test suite
python -m unittest discover -s tests

# Test execution output
# Ran 3 tests in 0.002s
# OK
```

Continuous integration runs automatically on every commit and pull request across Ubuntu and Windows runners via GitHub Actions.

---

## Roadmap

- [x] Initial release with CLI and JSON/Markdown export.
- [x] PEP 621 packaging and Windows cp1252 encoding hardening.
- [ ] Integration with Playwright for authenticated hydration sessions.
- [ ] Automated visual regression screenshot diffing during hydration.
- [ ] WebAudits.pro webhook dispatch for scheduled CI regression alerts.

---

## License

MIT License. See [LICENSE](LICENSE) for full details.
