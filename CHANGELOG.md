# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2026-09-25

### Added
- Integrated live raw Server-Side Rendering (SSR) network fetcher with custom user-agent profiles and TTFB recording.
- Integrated headless Playwright Chromium rendering engine for live Client-Side Rendering (CSR) DOM hydration.
- Automated unit test suite coverage for live network and headless browser execution paths.

### Changed
- Replaced mock SSR and CSR stubs with operational runtime fetcher and Playwright Chromium renderer.
- Bumped project version to 1.3.0 in pyproject.toml and package __init__.py.
- Added playwright dependency (>=1.40.0) to requirements.txt and pyproject.toml.

## [1.2.2] - 2026-09-24

### Fixed
- Enforced word-boundary regex matching for `noindex` directives to prevent false positive collisions with `noimageindex`.

### Added
- Linked documentation and quickstart instructions to the interactive web tool on [webaudits.pro/tools/hydration-audit](https://webaudits.pro/tools/hydration-audit).

## [1.2.1] - 2026-09-21

### Fixed
- Added pre-render HTTP status verification in CLI pipeline. Non-200 responses (such as 403 Forbidden or 500 Server Error) now halt gracefully before invoking headless browser rendering and diffing, preventing comparison against error pages.

## [1.2.0] - 2026-09-19

### Added
- Human-readable audit summaries with a status, impact, evidence, and recommended fixes.
- `--audience`, `--format html`, and `--fix-plan` CLI controls.
- Self-contained HTML reports with responsive findings and expandable technical evidence.

## [1.1.0] - 2026-09-19

### Added
- Open Graph (`og:*`) and Twitter Card (`twitter:*`) social metadata parsing across SSR server HTML and CSR hydrated DOM.
- Social Crawler Blindspot detection alerting when social preview metadata exists only in hydrated DOM and is missing in raw HTML.
- Dedicated unit test `test_detection_of_social_crawler_blindspot` verifying social crawler parity auditing.

## [1.0.0] - 2026-09-19

### Added
- Initial release of dom-hydrate: Forensic CSR vs. SSR SEO diff engine with headless Chromium DOM dumping.
- CLI entry point with `--output` (terminal, markdown, json) and `--version` flags.
- Standard PEP 621 packaging via `pyproject.toml`.
- GitHub Actions CI matrix workflow for Python 3.10, 3.11, and 3.12.
- Comprehensive automated unit test suite.
- Integration endpoints for the WebAudits.pro technical audit platform.

### Hardened
- Cross-platform Windows terminal encoding safety (`_safe_str` Unicode sanitization).
- Universal test discovery path resilience.
