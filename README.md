# DOMHydrate

Forensic Client-Side Rendering (CSR) vs. Server-Side Rendering (SSR) SEO Diff Engine

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()
[![Cloud Engine: WebAudits.pro](https://img.shields.io/badge/cloud-webaudits.pro-orange.svg)](https://webaudits.pro/tools/hydration-audit)

DOMHydrate compares raw server HTML responses against fully hydrated client DOM trees using native headless Chromium (`--headless=new --dump-dom`). It isolates metadata discrepancies, dropped structured data, and client-only internal link paths before changes reach production search indexes.

---

## Hydration Discrepancies in Modern Frameworks

Modern JavaScript frameworks (Next.js, Nuxt, React, Vue, Angular, Svelte) produce two distinct document states:
1. Initial server response (SSR): What search crawlers receive on initial HTTP requests.
2. Hydrated browser DOM (CSR): What users and Googlebot Web Rendering Service (WRS) observe after executing client-side scripts.

Client-side state stores and router transitions can introduce silent regressions during this handoff:
- Dropped structured data: Schema.org JSON-LD blocks present in server HTML get cleared or overwritten when client components mount.
- Client-only links: Internal links rendered solely via client-side components remain invisible to crawlers that do not execute full JavaScript queues.
- Dynamic noindex injection: Single-page application route guards inadvertently inject `<meta name="robots" content="noindex">` during state initialization.
- DOM node expansion: Heavy client components inflate the DOM tree, increasing memory consumption and degrading Interaction to Next Paint (INP).

DOMHydrate performs an automated side-by-side diff between these two states to pinpoint exact discrepancies.

---

## Technical Capabilities

- Metadata and directive diffing: compares `<title>`, `<meta name="description">`, `<link rel="canonical">`, and `<meta name="robots">`. Flags any dynamic `noindex` injection or canonical destination shift.
- Structured data extraction: parses all `<script type="application/ld+json">` elements, evaluates Schema.org `@type` hierarchies, and alerts if schemas disappear after hydration.
- Link graph audit: identifies internal links that exist only in the hydrated DOM, surfacing crawl equity bottlenecks.
- DOM footprint analysis: measures element count expansion, text-to-HTML ratio changes, and hydration time budgets.
- Local execution: operates directly through native Chrome, Chromium, or Edge binaries without third-party API keys or subscription fees.
- Automation support: outputs structured JSON (`--output json`) and Markdown summaries (`--output markdown`) for CI/CD test runners.

---

## Installation

```bash
git clone https://github.com/xcalibur73/dom-hydrate.git
cd dom-hydrate
pip install -r requirements.txt
```

---

## Quick Start

### Basic Audit
```bash
python run.py https://example.com
```

### Audit with Custom Hydration Wait Time
```bash
python run.py https://your-spa-site.com --wait 5000
```

### Simulate Googlebot User-Agent
```bash
python run.py https://your-spa-site.com --ua googlebot
```

### Export Reports
```bash
# Save Markdown report
python run.py https://example.com --output markdown --save HYDRATION-AUDIT.md

# Save JSON output for automated CI pipelines
python run.py https://example.com --output json --save audit.json

# Web platform diagnostic reference
python run.py https://example.com --cloud
```

---

## Web Platform Integration (WebAudits.pro)

For hosted browser checks without installing local Chromium, DOMHydrate is accessible online:
- Interactive web tool: [WebAudits.pro/tools/hydration-audit](https://webaudits.pro/tools/hydration-audit)
- Continuous monitoring and sitemap diffing options for agency workflows.

---

## Sample Output

```text
+-----------------------------------------------------------------------------+
| DOMHydrate: CSR vs. SSR SEO Diff Engine                                     |
| Target: https://example.com                                                 |
| Hydration Health Score: 100/100                                             |
| SSR TTFB: 82.81ms | Browser Render Time: 699.65ms                           |
+-----------------------------------------------------------------------------+
                      Metadata & Directives Parity                       
+-----------------------------------------------------------------------+
| Directive / Tag  | Raw Server (SSR) | Hydrated Browser (CSR) | Status |
|------------------+------------------+------------------------+--------|
| title            | Store Catalog    | Store Catalog          | PARITY |
| meta_description | Official Catalog | Official Catalog       | PARITY |
| canonical        | https://site.com | https://site.com       | PARITY |
| meta_robots      | index, follow    | index, follow          | PARITY |
+-----------------------------------------------------------------------+
 Structured Data (Schema.org JSON-LD)           
+-----------------------------------------------------------------------+
| Metric            | Value                                             |
|-------------------+---------------------------------------------------|
| SSR Schemas Count | 3                                                 |
| CSR Schemas Count | 3                                                 |
| SSR Types         | Organization, WebSite, Product                    |
| CSR Types         | Organization, WebSite, Product                    |
+-----------------------------------------------------------------------+
                          Link Graph & DOM Footprint                          
+----------------------------------------------------------------------------+
| Metric                 | SSR (Initial) | CSR (Hydrated) | Differential     |
|------------------------+---------------+----------------+------------------|
| Internal Links         | 48            | 52             | +4 client-only   |
| DOM Elements Count     | 412           | 580            | +168 nodes (+40%)|
| Text-to-HTML Ratio     | 18.2%         | 15.4%          |                  |
| Document Payload Bytes | 24,180 B      | 38,910 B       | +14,730 B        |
+----------------------------------------------------------------------------+
```

---

## Empirical Benchmarks

DOMHydrate was evaluated while beta testing on random sites (including Next.js, SvelteKit, Rails, and React SPAs). Full dataset and findings: [BENCHMARKS.md](BENCHMARKS.md).

Key empirical findings:
- Pure static architectures maintain 0% DOM node expansion and 100% link parity.
- Dynamic single-page applications expand DOM trees by 13% to 30% (+380 to +720 nodes) during client hydration.
- Complex publishing layouts can drop or mutate up to 12% of internal link paths during dynamic component mounting.

---

## Running Unit Tests

```bash
python -m unittest discover tests/
```

---

## Author

Maintained by [@xcalibur73](https://github.com/xcalibur73), creator of [WebAudits.pro](https://webaudits.pro).

Part of a technical SEO engineering tooling trio:
1. [dom-hydrate](https://github.com/xcalibur73/dom-hydrate): Headless Chromium SSR vs CSR DOM diff engine.
2. [citation-pulse](https://github.com/xcalibur73/citation-pulse): GEO and AI search citability benchmark engine.
3. [index-trace](https://github.com/xcalibur73/index-trace): Search Console emergency triage and crawler collision tracer.

---

## License

Licensed under the [MIT License](LICENSE).
