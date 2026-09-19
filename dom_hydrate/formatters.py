"""
Output formatters for dom-hydrate (Terminal Rich Tables, Markdown, and JSON).
"""

import html
from typing import Dict, Any

from .human_report import build_human_report

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


def _safe_str(text: Any) -> str:
    if not isinstance(text, str):
        text = str(text or "")
    text = (
        text.replace("\u2192", "->")
        .replace("\u2190", "<-")
        .replace("\u2194", "<->")
        .replace("\u2022", "*")
        .replace("\u2019", "'")
        .replace("\u2018", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2014", "-")
        .replace("\u2013", "-")
    )
    return text.encode("ascii", errors="replace").decode("ascii")


def _print_human_summary(report: Dict[str, Any], fix_plan: bool) -> None:
    if HAS_RICH:
        color = {"Pass": "green", "Needs attention": "yellow", "Critical": "red"}[report["status"]]
        content = Text()
        content.append(f"{report['status']}: ", style=f"bold {color}")
        content.append(report["summary"])
        console = Console()
        console.print(Panel(content, title="Plain-language result", border_style=color))
        if report["findings"]:
            table = Table(title="Fix plan" if fix_plan else "Findings", show_header=True, header_style="bold")
            table.add_column("Priority", style="bold")
            table.add_column("Finding")
            table.add_column("Recommended fix")
            for finding in report["findings"]:
                table.add_row(finding["severity"], finding["title"], finding["recommended_fix"])
            console.print(table)
        return

    print(f"\n{report['status']}: {report['summary']}")
    if fix_plan:
        for finding in report["findings"]:
            print(f"- {finding['title']}: {finding['recommended_fix']}")


def print_terminal_report(
    diff: Dict[str, Any],
    fetch_meta: Dict[str, Any],
    render_meta: Dict[str, Any],
    audience: str = "human",
    fix_plan: bool = False,
):
    human_report = build_human_report(diff)
    _print_human_summary(human_report, fix_plan)
    if audience == "human":
        return

    if not HAS_RICH:
        print(f"\n=== DOMHydrate Audit: {diff['url']} ===")
        print(f"Health Score: {diff['health_score']}/100")
        if diff['robots_danger']:
            print("ALERT: Client-side JS injected NOINDEX!")
        print(f"SSR Bytes: {fetch_meta.get('content_length_bytes')} | CSR Bytes: {render_meta.get('content_length_bytes')}")
        print(f"Metadata Diffs: {len(diff['metadata']['diffs'])}")
        for d in diff['metadata']['diffs']:
            print(f"- {d['field']}: SSR='{d['ssr']}' vs CSR='{d['csr']}'")
        return

    console = Console()

    # Header Panel
    score = diff['health_score']
    score_color = "green" if score >= 85 else ("yellow" if score >= 60 else "red")
    header_text = Text()
    header_text.append("DOMHydrate: CSR vs. SSR SEO Diff Engine\n", style="bold cyan")
    header_text.append(f"Target: {_safe_str(diff['url'])}\n", style="bold white")
    header_text.append(f"Hydration Health Score: {score}/100\n", style=f"bold {score_color}")
    header_text.append(f"SSR TTFB: {fetch_meta.get('ttfb_ms')}ms | Browser Render Time: {render_meta.get('render_time_ms')}ms", style="dim")

    console.print(Panel(header_text, border_style="cyan"))

    if diff["robots_danger"]:
        console.print(Panel("[bold red]CRITICAL ALERT: Client-side hydration injected NOINDEX! Search engines executing JavaScript will drop this URL from the index.[/bold red]", border_style="red"))

    # Metadata Table
    table = Table(title="Metadata & Directives Parity", show_header=True, header_style="bold magenta")
    table.add_column("Directive / Tag", style="cyan")
    table.add_column("Raw Server (SSR)", style="white")
    table.add_column("Hydrated Browser (CSR)", style="white")
    table.add_column("Status", style="bold")

    meta_diff_map = {d["field"]: d for d in diff["metadata"]["diffs"]}

    for field in ["title", "meta_description", "canonical", "meta_robots"]:
        s_val = diff["metadata"]["ssr"].get(field, "")
        c_val = diff["metadata"]["csr"].get(field, "")
        if field in meta_diff_map:
            sev = meta_diff_map[field]["severity"]
            status = f"[red]MISMATCH ({sev})[/red]"
        else:
            status = "[green]PARITY[/green]"

        # Truncate long strings
        s_val_safe = _safe_str(s_val)
        c_val_safe = _safe_str(c_val)
        s_disp = (s_val_safe[:45] + "...") if len(s_val_safe) > 45 else (s_val_safe or "[dim]empty[/dim]")
        c_disp = (c_val_safe[:45] + "...") if len(c_val_safe) > 45 else (c_val_safe or "[dim]empty[/dim]")
        table.add_row(field, s_disp, c_disp, status)

    console.print(table)

    # Social Crawler Parity Table
    social_data = diff.get("social", {})
    if social_data.get("ssr") or social_data.get("csr"):
        soc_table = Table(title="Social Crawler Parity (Open Graph & Twitter Cards)", show_header=True, header_style="bold magenta")
        soc_table.add_column("Property / Tag", style="cyan")
        soc_table.add_column("Raw Server (SSR)", style="white")
        soc_table.add_column("Hydrated Browser (CSR)", style="white")
        soc_table.add_column("Social Bot Parity", style="bold")

        diff_tags = {d["tag"]: d for d in social_data.get("diffs", [])}
        for tag in ["og:title", "og:description", "og:image", "og:url", "twitter:card"]:
            s_val = social_data.get("ssr", {}).get(tag, "")
            c_val = social_data.get("csr", {}).get(tag, "")
            if tag in diff_tags:
                d = diff_tags[tag]
                if d.get("blindspot"):
                    status = "[red]BLINDSPOT (Missing SSR)[/red]"
                else:
                    status = "[yellow]DRIFT[/yellow]"
            elif s_val:
                status = "[green]PARITY[/green]"
            else:
                status = "[dim]NOT SET[/dim]"

            s_disp = (_safe_str(s_val)[:40] + "...") if len(s_val) > 40 else (_safe_str(s_val) or "[dim]empty[/dim]")
            c_disp = (_safe_str(c_val)[:40] + "...") if len(c_val) > 40 else (_safe_str(c_val) or "[dim]empty[/dim]")
            soc_table.add_row(tag, s_disp, c_disp, status)

        console.print(soc_table)

    if diff.get("social_crawler_blindspot"):
        console.print(Panel("[yellow]WARNING: Social Crawler Blindspot Detected! Open Graph / Twitter tags are populated only during client-side hydration. Non-JavaScript social crawlers (Facebook, X, LinkedIn, Slack) will see blank previews.[/yellow]", border_style="yellow"))

    # Structured Data Table
    schema_table = Table(title="Structured Data (Schema.org JSON-LD)", show_header=True, header_style="bold yellow")
    schema_table.add_column("Metric", style="cyan")
    schema_table.add_column("Value", style="white")

    schema_table.add_row("SSR Schemas Count", str(diff["schemas"]["ssr_count"]))
    schema_table.add_row("CSR Schemas Count", str(diff["schemas"]["csr_count"]))
    schema_table.add_row("SSR Types", ", ".join(diff["schemas"]["ssr_types"]) or "None")
    schema_table.add_row("CSR Types", ", ".join(diff["schemas"]["csr_types"]) or "None")

    if diff["schemas"]["dropped_on_hydration"]:
        schema_table.add_row("[red]Dropped on Hydration[/red]", f"[bold red]{', '.join(diff['schemas']['dropped_on_hydration'])}[/bold red]")
    if diff["schemas"]["injected_on_hydration"]:
        schema_table.add_row("[green]Injected on Hydration[/green]", f"[green]{', '.join(diff['schemas']['injected_on_hydration'])}[/green]")

    console.print(schema_table)

    # Link Graph & DOM Footprint Table
    stat_table = Table(title="Link Graph & DOM Footprint", show_header=True, header_style="bold blue")
    stat_table.add_column("Metric", style="cyan")
    stat_table.add_column("SSR (Initial)", style="white")
    stat_table.add_column("CSR (Hydrated)", style="white")
    stat_table.add_column("Differential", style="bold")

    stat_table.add_row("Internal Links", str(diff["links"]["ssr_internal_count"]), str(diff["links"]["csr_internal_count"]), f"+{diff['links']['csr_only_internal_total']} client-only")
    stat_table.add_row("DOM Elements Count", str(diff["dom_stats"]["ssr"]["node_count"]), str(diff["dom_stats"]["csr"]["node_count"]), f"+{diff['dom_stats']['node_bloat']} nodes (+{diff['dom_stats']['node_bloat_percent']}%)")
    stat_table.add_row("Text-to-HTML Ratio", f"{diff['dom_stats']['ssr']['text_ratio_percent']}%", f"{diff['dom_stats']['csr']['text_ratio_percent']}%", "")
    stat_table.add_row("Document Payload Bytes", f"{fetch_meta.get('content_length_bytes'):,} B", f"{render_meta.get('content_length_bytes'):,} B", f"+{render_meta.get('content_length_bytes') - fetch_meta.get('content_length_bytes'):,} B")

    console.print(stat_table)


def export_html_report(diff: Dict[str, Any], fetch_meta: Dict[str, Any], render_meta: Dict[str, Any]) -> str:
    """Return a self-contained HTML report with plain-language findings."""
    report = build_human_report(diff)
    status_class = report["status"].lower().replace(" ", "-")
    findings = "".join(
        "<article class='finding'>"
        f"<p class='severity {html.escape(item['severity'].lower().replace(' ', '-'))}'>{html.escape(item['severity'])}</p>"
        f"<h2>{html.escape(item['title'])}</h2>"
        f"<p><strong>Why it matters:</strong> {html.escape(item['impact'])}</p>"
        f"<p><strong>Evidence:</strong> {html.escape(item['evidence'])}</p>"
        f"<p><strong>Recommended fix:</strong> {html.escape(item['recommended_fix'])}</p>"
        "</article>"
        for item in report["findings"]
    ) or "<p class='empty'>No parity issues were detected for the audited signals.</p>"
    metadata_rows = "".join(
        f"<tr><th>{html.escape(field)}</th><td>{html.escape(str(diff['metadata']['ssr'].get(field, '')))}</td>"
        f"<td>{html.escape(str(diff['metadata']['csr'].get(field, '')))}</td></tr>"
        for field in ["title", "meta_description", "canonical", "meta_robots"]
    )
    return f"""<!doctype html>
<html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>
<title>DOMHydrate report</title><style>
:root {{ color-scheme: light; --ink:#20201e; --muted:#716c64; --line:#ddd7ce; --paper:#f7f4ee; --panel:#fff; --accent:#b76345; --good:#216e4e; --warn:#9a6700; --bad:#b42318; }}
* {{ box-sizing:border-box; }} body {{ margin:0; background:var(--paper); color:var(--ink); font:16px/1.55 Georgia, serif; }} main {{ width:min(920px, calc(100% - 32px)); margin:48px auto; }} h1,h2 {{ line-height:1.15; }} .eyebrow,.severity {{ margin:0; font:700 12px/1.2 Arial,sans-serif; letter-spacing:.08em; text-transform:uppercase; }} .status {{ border-left:6px solid var(--accent); padding:24px; background:var(--panel); }} .pass {{ border-color:var(--good); }} .needs-attention {{ border-color:var(--warn); }} .critical {{ border-color:var(--bad); }} .finding,details {{ margin-top:16px; padding:20px 24px; background:var(--panel); border:1px solid var(--line); }} .severity.pass {{ color:var(--good); }} .severity.needs-attention {{ color:var(--warn); }} .severity.critical {{ color:var(--bad); }} table {{ width:100%; border-collapse:collapse; margin-top:12px; font-family:Arial,sans-serif; font-size:14px; }} th,td {{ padding:12px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; overflow-wrap:anywhere; }} summary {{ cursor:pointer; font-weight:700; }} @media (max-width:600px) {{ main {{ width:min(100% - 24px, 920px); margin:24px auto; }} .status,.finding,details {{ padding:18px; }} }}
</style></head><body><main>
<p class='eyebrow'>DOMHydrate report</p><h1>{html.escape(str(diff['url']))}</h1>
<section class='status {status_class}'><p class='severity {status_class}'>{html.escape(report['status'])}</p><p>{html.escape(report['summary'])}</p><p>Hydration health score: {html.escape(str(diff['health_score']))}/100</p></section>
<section><h2>Findings</h2>{findings}</section>
<details><summary>Technical evidence</summary><table><thead><tr><th>Signal</th><th>Server HTML</th><th>Hydrated DOM</th></tr></thead><tbody>{metadata_rows}</tbody></table><p>SSR TTFB: {html.escape(str(fetch_meta.get('ttfb_ms')))} ms. Browser render time: {html.escape(str(render_meta.get('render_time_ms')))} ms.</p></details>
</main></body></html>"""

def export_markdown(diff: Dict[str, Any], fetch_meta: Dict[str, Any], render_meta: Dict[str, Any]) -> str:
    md = []
    md.append(f"# DOMHydrate Forensic Report: {diff['url']}\n")
    md.append(f"**Hydration Health Score**: {diff['health_score']}/100\n")
    md.append(f"- **SSR TTFB**: {fetch_meta.get('ttfb_ms')}ms")
    md.append(f"- **Browser Hydration Time**: {render_meta.get('render_time_ms')}ms")
    md.append(f"- **Initial HTML Payload**: {fetch_meta.get('content_length_bytes')} bytes")
    md.append(f"- **Rendered DOM Payload**: {render_meta.get('content_length_bytes')} bytes\n")

    if diff["robots_danger"]:
        md.append("> [!CAUTION]\n> **Client-side hydration injected NOINDEX!** Search engines executing JavaScript will drop this URL from indexation.\n")

    md.append("## 1. Metadata & Directives Parity\n")
    md.append("| Directive | Server (SSR) | Hydrated (CSR) | Status |")
    md.append("|:---|:---|:---|:---|")
    meta_diff_map = {d["field"]: d for d in diff["metadata"]["diffs"]}
    for f in ["title", "meta_description", "canonical", "meta_robots"]:
        s_val = diff["metadata"]["ssr"].get(f, "") or "*(empty)*"
        c_val = diff["metadata"]["csr"].get(f, "") or "*(empty)*"
        status = "MISMATCH" if f in meta_diff_map else "PARITY"
        md.append(f"| **{f}** | `{s_val}` | `{c_val}` | **{status}** |")

    md.append("\n## 2. Structured Data (Schema.org JSON-LD)\n")
    md.append(f"- **SSR Schema Entities**: {', '.join(diff['schemas']['ssr_types']) or 'None'}")
    md.append(f"- **CSR Schema Entities**: {', '.join(diff['schemas']['csr_types']) or 'None'}")
    if diff["schemas"]["dropped_on_hydration"]:
        md.append(f"- **Dropped during hydration**: `{', '.join(diff['schemas']['dropped_on_hydration'])}`")
    if diff["schemas"]["injected_on_hydration"]:
        md.append(f"- **Injected client-side only**: `{', '.join(diff['schemas']['injected_on_hydration'])}`")

    md.append("\n## 3. Link Graph & Crawl Discovery\n")
    md.append(f"- **SSR Internal Links**: {diff['links']['ssr_internal_count']}")
    md.append(f"- **CSR Internal Links**: {diff['links']['csr_internal_count']}")
    md.append(f"- **Client-Only Internal Links**: {diff['links']['csr_only_internal_total']} (invisible to non-JS crawlers)")
    md.append(f"- **Dropped Links**: {diff['links']['dropped_internal_total']}")

    return "\n".join(md)
