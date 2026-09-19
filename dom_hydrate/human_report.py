"""Human-readable report data for DOMHydrate audits."""

from typing import Any


def build_human_report(diff: dict[str, Any]) -> dict[str, Any]:
    """Translate a DOM diff into status, summary, and action-ready findings."""
    findings: list[dict[str, str]] = []

    if diff["robots_danger"]:
        findings.append({
            "severity": "Critical",
            "title": "Hydration adds a noindex directive",
            "impact": "Search engines that render JavaScript can remove this page from their index.",
            "evidence": "The hydrated DOM contains noindex while the server HTML does not.",
            "recommended_fix": "Render the intended robots directive in the server HTML and prevent client code from adding noindex.",
        })

    for mismatch in diff["metadata"]["diffs"]:
        field = mismatch["field"].replace("_", " ")
        severity = "Critical" if mismatch["severity"] == "CRITICAL" else "Needs attention"
        findings.append({
            "severity": severity,
            "title": f"{field.title()} changes after hydration",
            "impact": "Crawlers can receive different page signals depending on whether they run JavaScript.",
            "evidence": f"Server: {mismatch['ssr'] or '(empty)'} | Hydrated: {mismatch['csr'] or '(empty)'}",
            "recommended_fix": f"Render the intended {field} value in the initial HTML and keep it stable after hydration.",
        })

    dropped_schemas = diff["schemas"]["dropped_on_hydration"]
    if dropped_schemas:
        findings.append({
            "severity": "Needs attention",
            "title": "Structured data disappears after hydration",
            "impact": "Search engines can receive inconsistent Schema.org entities for this page.",
            "evidence": f"Dropped types: {', '.join(dropped_schemas)}.",
            "recommended_fix": "Keep the JSON-LD scripts in the rendered document after client code completes.",
        })

    if diff["social_crawler_blindspot"]:
        findings.append({
            "severity": "Needs attention",
            "title": "Social preview metadata is client-only",
            "impact": "Social crawlers that do not execute JavaScript can show blank or incomplete previews.",
            "evidence": "One or more Open Graph or Twitter tags appear only after hydration.",
            "recommended_fix": "Render Open Graph and Twitter Card tags in the server HTML.",
        })

    dropped_links = diff["links"]["dropped_internal_total"]
    if dropped_links:
        findings.append({
            "severity": "Needs attention",
            "title": "Internal links disappear after hydration",
            "impact": "Crawlers can miss navigation paths that exist in the initial HTML.",
            "evidence": f"{dropped_links} internal link(s) are present in server HTML but absent after hydration.",
            "recommended_fix": "Keep crawlable navigation links in the post-hydration DOM.",
        })

    if any(item["severity"] == "Critical" for item in findings):
        status = "Critical"
        summary = "Hydration changes signals that can block indexing or change canonical page interpretation."
    elif findings:
        status = "Needs attention"
        summary = "Hydration changes page signals that crawlers and social platforms can interpret differently."
    else:
        status = "Pass"
        summary = "The server HTML and hydrated DOM keep the audited SEO signals aligned."

    return {"status": status, "summary": summary, "findings": findings}
