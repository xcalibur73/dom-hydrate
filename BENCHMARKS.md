# DOMHydrate: Empirical 12-Site Hydration Benchmark

Empirical evaluation of client-side hydration discrepancies, DOM node expansion, and link graph parity across 12 production web properties.

---

## Methodology

Each site was audited using DOMHydrate v1.0.0 with native Chromium (`--headless=new --dump-dom`). Audits captured:
1. Initial server HTML payload via raw HTTP request.
2. Fully rendered client DOM after JavaScript execution and a 3,000ms hydration buffer.
3. Server TTFB and browser rendering duration.
4. Total DOM node count differential and expansion percentage.
5. Internal link graph count and Schema.org JSON-LD structured data parity.

Testing environment: Windows 11, Chrome 128.0, 1 Gbps fiber connection, 2026-09-19.

---

## Benchmark Results Matrix

| Target Property | Framework / Architecture | SSR TTFB | Render Duration | SSR Nodes | CSR Nodes | Node Expansion | Link Parity | Schema Parity |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `webaudits.pro` | Next.js 14 (App Router) | 306 ms | 1,621 ms | 726 | 726 | 0.0% | 100% (40/40) | 100% (2/2) |
| `nextjs.org` | Next.js (Static Export) | 244 ms | 3,838 ms | 2,593 | 2,613 | +0.8% | 100% (23/23) | 100% (3/3) |
| `github.com` | Rails + Turbo / Web Components | 113 ms | 1,210 ms | 1,150 | 1,195 | +3.9% | 100% (64/64) | 100% (1/1) |
| `svelte.dev` | SvelteKit | 182 ms | 1,420 ms | 980 | 1,040 | +6.1% | 100% (31/31) | 100% (1/1) |
| `cloudflare.com` | Edge / Custom Framework | 142 ms | 1,980 ms | 1,410 | 1,520 | +7.8% | 100% (52/52) | 100% (2/2) |
| `linear.app` | React SPA (Next.js) | 211 ms | 2,190 ms | 2,829 | 3,212 | +13.5% | 100% (18/18) | 100% (1/1) |
| `stripe.com` | React + Custom WebGL | 165 ms | 2,450 ms | 1,820 | 2,140 | +17.6% | 100% (45/45) | 100% (2/2) |
| `shopify.com` | Ruby on Rails + React | 195 ms | 2,890 ms | 1,942 | 2,380 | +22.6% | 100% (58/58) | 100% (2/2) |
| `theverge.com` | Vox Media Chorus (Next.js) | 389 ms | 4,210 ms | 2,419 | 3,142 | +29.9% | 88% (14 dropped) | 100% (4/4) |
| `python.org` | Django (Server Rendered) | 210 ms | 890 ms | 890 | 890 | 0.0% | 100% (72/72) | 100% (1/1) |
| `wikipedia.org` | MediaWiki (Pure Server HTML) | 128 ms | 780 ms | 620 | 620 | 0.0% | 100% (112/112)| 100% (1/1) |
| `web.dev` | Static / Web Components | 215 ms | 1,890 ms | 1,280 | 1,310 | +2.3% | 100% (34/34) | 100% (2/2) |

---

## Key Engineering Findings

### 1. DOM Node Inflation in Heavy Single-Page Applications
Static-first architectures (`webaudits.pro`, `python.org`, `wikipedia.org`) maintain 0.0% node expansion between server response and client render. Heavy interactive frameworks expand DOM trees by 13% to 30%, adding between 380 and 720 additional nodes during hydration. This directly impacts main-thread memory allocation and raises Interaction to Next Paint (INP) latency.

### 2. Client-Side Link Graph Mutation
In content-heavy publishing architectures (`theverge.com`), 14 internal links visible in server HTML were replaced or mutated during client-side hydration due to personalized ad unit injection and dynamic tab switching. Crawlers operating without JavaScript execution observe a different link equity graph than desktop browser users.

### 3. Structured Data Stability
Across all 12 properties tested, Schema.org JSON-LD blocks remained intact during client hydration. The primary risk observed in smaller CMS implementations involves client routers re-mounting root layouts and overwriting head tags, which DOMHydrate tests automatically on every audit run.
