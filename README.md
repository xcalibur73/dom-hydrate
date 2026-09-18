# DOMHydrate 💧

> **Forensic Client-Side Rendering (CSR) vs. Server-Side Rendering (SSR) SEO Diff Engine**  
> Catch silent search regressions, stripped Schema.org entities, dropped internal links, and accidental client-side `noindex` injections before they devastate organic visibility.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()

---

## 🛑 The Hidden SEO Problem with Modern Frameworks

Modern JavaScript frameworks (Next.js, Nuxt, React, Vue, Angular, Svelte) render content in two stages:
1. **The Initial Server Response (SSR)**: What traditional web crawlers and lightweight bots receive over raw HTTP.
2. **The Hydrated Browser DOM (CSR)**: What users and Googlebot's second-wave Web Rendering Service (WRS) see after executing JavaScript.

When hydration desynchronizes, catastrophic SEO failures occur silently:
* **Stripped Schemas**: Rich Schema.org JSON-LD tags present in server templates get overwritten or stripped by client-side state stores.
* **Client-Only Internal Links**: Navigation links populated solely via client components remain invisible to crawlers that do not execute full JavaScript queues.
* **Accidental `noindex` Injections**: Single-Page App router scripts mistakenly inject `<meta name="robots" content="noindex">` during hydration.
* **DOM Node Explosion**: Heavy client components inflate the DOM by 300%+, spiking memory and ruining Core Web Vitals (INP and Total Blocking Time).

**DOMHydrate** executes a forensic side-by-side diff between raw HTTP and fully hydrated headless Chromium output to pinpoint these regressions in seconds.

---

## ⚡ Key Features

* **Metadata & Directive Parity**: Diffs `<title>`, `<meta name="description">`, `<link rel="canonical">`, and `<meta name="robots">`. Instantly raises a critical alert if client hydration injects `noindex` or alters canonical destinations.
* **Structured Data (Schema.org) Inspector**: Extracts all `<script type="application/ld+json">` blocks, evaluates `@type` hierarchies, and alerts if schemas are dropped during hydration.
* **Link Graph Differential**: Catches internal links that only exist after client-side hydration, highlighting crawl equity bottlenecks.
* **DOM Footprint & Node Bloat Analysis**: Measures DOM element count increases, text-to-HTML ratio changes, and hydration time budgets.
* **Zero SaaS Dependencies**: Leverages your system's native Chrome, Chromium, or Edge binary with `--headless=new` with zero subscription fees or external API keys.
* **CI/CD Ready**: Outputs structured JSON (`--output json`) and executive Markdown reports (`--output markdown`).

---

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/xcalibur73/dom-hydrate.git
cd dom-hydrate

# Install dependencies
pip install -r requirements.txt
```

### Basic Audit

```bash
# Run a quick audit on any website
python run.py https://example.com

# Audit an SPA with a custom hydration wait time (default: 4000ms)
python run.py https://your-spa-site.com --wait 5000

# Audit using Googlebot User-Agent
python run.py https://your-spa-site.com --ua googlebot
```

### Exporting Reports

```bash
# Generate an executive markdown audit
python run.py https://example.com --output markdown --save HYDRATION-AUDIT.md

# Generate raw JSON for automated testing pipelines
python run.py https://example.com --output json --save audit.json
```

---

## 📊 Sample Output

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

## 🧪 Running Unit Tests

```bash
python -m unittest discover tests/
```

---

## 👤 Author

**Sadikeen Firoz**
* Portfolio: [WebAudits.pro](https://webaudits.pro)
* GitHub: [@xcalibur73](https://github.com/xcalibur73)
* Focus: Technical SEO, Core Web Vitals, and Generative Engine Optimization (GEO)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
