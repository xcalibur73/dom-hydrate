"""
Command-Line Interface for DOMHydrate.
"""

import argparse
import json
import sys
from .fetcher import fetch_ssr
from .renderer import render_csr
from .diff_engine import diff_ssr_csr
from .formatters import export_html_report, export_markdown, print_terminal_report

def main(args: list[str] | None = None) -> int:
    from . import __version__
    parser = argparse.ArgumentParser(
        prog="dom-hydrate",
        description="DOMHydrate: Forensic CSR vs. SSR SEO Diff Engine."
    )
    parser.add_argument("url", nargs="?", help="Target website URL to inspect")
    parser.add_argument(
        "--version",
        action="version",
        version=f"DOMHydrate v{__version__}"
    )
    parser.add_argument("--wait", type=int, default=4000, help="Client-side hydration wait time in ms (default: 4000)")
    parser.add_argument("--ua", default="chrome", choices=["chrome", "googlebot", "mobile"], help="User-Agent profile")
    parser.add_argument("--output", "--format", dest="output", choices=["terminal", "markdown", "json", "html"], default="terminal", help="Output format")
    parser.add_argument("--audience", choices=["human", "expert"], default="human", help="Report detail level")
    parser.add_argument("--fix-plan", action="store_true", help="Emphasize recommended fixes in terminal output")
    parser.add_argument("--save", help="Optional path to save output file")
    parser.add_argument("--cloud", action="store_true", help="Generate continuous monitoring audit link on WebAudits.pro")

    args = parser.parse_args(args)
    if not args.url:
        parser.print_help()
        return 0

    try:
        print(f"[*] Fetching SSR HTML for {args.url} ...", file=sys.stderr)
        ssr_data = fetch_ssr(args.url, user_agent_type=args.ua)

        print(f"[*] Rendering CSR DOM in headless browser (wait: {args.wait}ms) ...", file=sys.stderr)
        csr_data = render_csr(args.url, wait_ms=args.wait)

        print(f"[*] Computing SEO parity differential ...", file=sys.stderr)
        diff = diff_ssr_csr(ssr_data["html"], csr_data["html"], args.url)

        if args.output == "terminal":
            print_terminal_report(diff, ssr_data, csr_data, audience=args.audience, fix_plan=args.fix_plan)
        elif args.output == "markdown":
            md = export_markdown(diff, ssr_data, csr_data)
            print(md)
            if args.save:
                with open(args.save, "w", encoding="utf-8") as f:
                    f.write(md)
                print(f"[+] Saved markdown audit to {args.save}", file=sys.stderr)
        elif args.output == "html":
            html_report = export_html_report(diff, ssr_data, csr_data)
            print(html_report)
            if args.save:
                with open(args.save, "w", encoding="utf-8") as f:
                    f.write(html_report)
                print(f"[+] Saved HTML audit to {args.save}", file=sys.stderr)
        elif args.output == "json":
            combined = {
                "diff": diff,
                "ssr_meta": {k: v for k, v in ssr_data.items() if k != "html"},
                "csr_meta": {k: v for k, v in csr_data.items() if k != "html"}
            }
            out_json = json.dumps(combined, indent=2)
            print(out_json)
            if args.save:
                with open(args.save, "w", encoding="utf-8") as f:
                    f.write(out_json)
                print(f"[+] Saved JSON audit to {args.save}", file=sys.stderr)

        if args.cloud:
            import urllib.parse
            cloud_url = f"https://webaudits.pro/tools/hydration-audit?url={urllib.parse.quote(args.url)}"
            print(f"\n[+] WebAudits.pro Cloud Link for CI/CD Hydration Monitoring:")
            print(f"    {cloud_url}")
            print(f"    Features: automated GitHub Actions regression testing, bulk URL diffing, Slack alerts.")
        elif args.output == "terminal":
            print(f"\n[i] WebAudits.pro Cloud Platform: Run with --cloud or visit https://webaudits.pro/tools/hydration-audit for CI/CD testing.", file=sys.stderr)

    except Exception as e:
        print(f"[!] Error: {e}", file=sys.stderr)
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
