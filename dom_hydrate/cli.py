"""
Command-Line Interface for DOMHydrate.
"""

import argparse
import json
import sys
from .fetcher import fetch_ssr
from .renderer import render_csr
from .diff_engine import diff_ssr_csr
from .formatters import print_terminal_report, export_markdown

def main():
    parser = argparse.ArgumentParser(
        description="DOMHydrate: Forensic CSR vs. SSR SEO Diff Engine."
    )
    parser.add_argument("url", help="Target website URL to inspect")
    parser.add_argument("--wait", type=int, default=4000, help="Client-side hydration wait time in ms (default: 4000)")
    parser.add_argument("--ua", default="chrome", choices=["chrome", "googlebot", "mobile"], help="User-Agent profile")
    parser.add_argument("--output", choices=["terminal", "markdown", "json"], default="terminal", help="Output format")
    parser.add_argument("--save", help="Optional path to save output file")

    args = parser.parse_args()

    try:
        print(f"[*] Fetching SSR HTML for {args.url} ...", file=sys.stderr)
        ssr_data = fetch_ssr(args.url, user_agent_type=args.ua)

        print(f"[*] Rendering CSR DOM in headless browser (wait: {args.wait}ms) ...", file=sys.stderr)
        csr_data = render_csr(args.url, wait_ms=args.wait)

        print(f"[*] Computing SEO parity differential ...", file=sys.stderr)
        diff = diff_ssr_csr(ssr_data["html"], csr_data["html"], args.url)

        if args.output == "terminal":
            print_terminal_report(diff, ssr_data, csr_data)
        elif args.output == "markdown":
            md = export_markdown(diff, ssr_data, csr_data)
            print(md)
            if args.save:
                with open(args.save, "w", encoding="utf-8") as f:
                    f.write(md)
                print(f"[+] Saved markdown audit to {args.save}", file=sys.stderr)
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

    except Exception as e:
        print(f"[!] Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
