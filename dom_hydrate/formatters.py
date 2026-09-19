"""
Output formatters for dom-hydrate (Terminal Rich Tables, Markdown, and JSON).
"""

import json
from typing import Dict, Any

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


def print_terminal_report(diff: Dict[str, Any], fetch_meta: Dict[str, Any], render_meta: Dict[str, Any]):
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
