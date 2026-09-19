"""
Core SEO Diff Engine for comparing SSR HTML against hydrated CSR DOM.
"""

import json
from typing import Dict, Any, List, Set, Tuple
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

def normalize_text(text: str) -> str:
    if not text:
        return ""
    return " ".join(text.split()).strip()

def extract_metadata(soup: BeautifulSoup) -> Dict[str, Any]:
    # Title
    title_el = soup.find("title")
    title = normalize_text(title_el.text) if title_el else ""

    # Meta Description
    desc_el = soup.find("meta", attrs={"name": lambda x: x and x.lower() == "description"})
    meta_desc = normalize_text(desc_el.get("content", "")) if desc_el else ""

    # Meta Robots
    robots_el = soup.find("meta", attrs={"name": lambda x: x and x.lower() == "robots"})
    meta_robots = normalize_text(robots_el.get("content", "")) if robots_el else ""

    # Canonical
    canon_el = soup.find("link", attrs={"rel": lambda x: x and "canonical" in [r.lower() for r in (x if isinstance(x, list) else [x])]})
    canonical = canon_el.get("href", "").strip() if canon_el else ""

    # H1
    h1s = [normalize_text(h.text) for h in soup.find_all("h1")]

    # Open Graph & Twitter Cards (Social Crawler Parity)
    def get_meta_prop(prop_name: str) -> str:
        el = soup.find("meta", attrs={"property": lambda x: x and x.lower() == prop_name.lower()})
        if not el:
            el = soup.find("meta", attrs={"name": lambda x: x and x.lower() == prop_name.lower()})
        return normalize_text(el.get("content", "")) if el else ""

    social_tags = {
        "og:title": get_meta_prop("og:title"),
        "og:description": get_meta_prop("og:description"),
        "og:image": get_meta_prop("og:image"),
        "og:url": get_meta_prop("og:url"),
        "twitter:card": get_meta_prop("twitter:card"),
        "twitter:title": get_meta_prop("twitter:title"),
        "twitter:description": get_meta_prop("twitter:description"),
        "twitter:image": get_meta_prop("twitter:image"),
    }

    return {
        "title": title,
        "meta_description": meta_desc,
        "meta_robots": meta_robots,
        "canonical": canonical,
        "h1s": h1s,
        "social_tags": social_tags
    }

def extract_json_ld(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    schemas = []
    scripts = soup.find_all("script", attrs={"type": "application/ld+json"})
    for s in scripts:
        raw = s.string or s.text or ""
        raw = raw.strip()
        if not raw:
            continue
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                schemas.extend(parsed)
            elif isinstance(parsed, dict):
                # Check for @graph
                if "@graph" in parsed and isinstance(parsed["@graph"], list):
                    schemas.extend(parsed["@graph"])
                else:
                    schemas.append(parsed)
        except Exception:
            schemas.append({"_parse_error": True, "_raw_snippet": raw[:120]})
    return schemas

def extract_links(soup: BeautifulSoup, base_url: str) -> Tuple[Set[str], Set[str]]:
    internal_links = set()
    external_links = set()
    base_netloc = urlparse(base_url).netloc.lower()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)
        # Strip fragment
        cleaned_url = parsed._replace(fragment="").geturl()

        if parsed.netloc.lower() == base_netloc or not parsed.netloc:
            internal_links.add(cleaned_url)
        else:
            external_links.add(cleaned_url)

    return internal_links, external_links

def calculate_dom_stats(soup: BeautifulSoup, raw_html: str) -> Dict[str, Any]:
    all_elements = soup.find_all(True)
    scripts = soup.find_all("script")
    text_content = normalize_text(soup.get_text())
    html_bytes = len(raw_html.encode("utf-8"))
    text_bytes = len(text_content.encode("utf-8"))
    ratio = round((text_bytes / html_bytes) * 100, 2) if html_bytes > 0 else 0.0

    return {
        "node_count": len(all_elements),
        "script_count": len(scripts),
        "text_length": len(text_content),
        "html_bytes": html_bytes,
        "text_ratio_percent": ratio
    }

def diff_ssr_csr(ssr_html: str, csr_html: str, base_url: str) -> Dict[str, Any]:
    ssr_soup = BeautifulSoup(ssr_html, "html.parser")
    csr_soup = BeautifulSoup(csr_html, "html.parser")

    # 1. Metadata
    ssr_meta = extract_metadata(ssr_soup)
    csr_meta = extract_metadata(csr_soup)

    meta_diffs = []
    for key in ["title", "meta_description", "meta_robots", "canonical"]:
        s_val = ssr_meta[key]
        c_val = csr_meta[key]
        if s_val != c_val:
            meta_diffs.append({
                "field": key,
                "ssr": s_val,
                "csr": c_val,
                "severity": "CRITICAL" if key in ["meta_robots", "canonical"] else "WARNING"
            })

    # Robots specific danger check
    robots_danger = False
    if "noindex" in csr_meta["meta_robots"].lower() and "noindex" not in ssr_meta["meta_robots"].lower():
        robots_danger = True

    # 2. Social Crawler Parity (Open Graph & Twitter Cards)
    social_diffs = []
    ssr_social = ssr_meta.get("social_tags", {})
    csr_social = csr_meta.get("social_tags", {})
    for tag_name, s_val in ssr_social.items():
        c_val = csr_social.get(tag_name, "")
        if s_val != c_val:
            social_diffs.append({
                "tag": tag_name,
                "ssr": s_val,
                "csr": c_val,
                "blindspot": not bool(s_val) and bool(c_val)
            })

    social_crawler_blindspot = any(d["blindspot"] for d in social_diffs)

    # 3. JSON-LD Schemas
    ssr_schemas = extract_json_ld(ssr_soup)
    csr_schemas = extract_json_ld(csr_soup)

    def get_types(schemas):
        types = []
        for s in schemas:
            t = s.get("@type", "Unknown")
            if isinstance(t, list):
                types.extend(t)
            else:
                types.append(str(t))
        return types

    ssr_types = get_types(ssr_schemas)
    csr_types = get_types(csr_schemas)

    dropped_schemas = [t for t in ssr_types if t not in csr_types]
    injected_schemas = [t for t in csr_types if t not in ssr_types]

    # 3. Links
    ssr_int, ssr_ext = extract_links(ssr_soup, base_url)
    csr_int, csr_ext = extract_links(csr_soup, base_url)

    csr_only_internal = csr_int - ssr_int
    dropped_internal = ssr_int - csr_int

    # 4. DOM Footprint
    ssr_stats = calculate_dom_stats(ssr_soup, ssr_html)
    csr_stats = calculate_dom_stats(csr_soup, csr_html)

    node_bloat = csr_stats["node_count"] - ssr_stats["node_count"]
    node_bloat_percent = round((node_bloat / max(1, ssr_stats["node_count"])) * 100, 1)

    # Health score calculation
    score = 100
    if robots_danger:
        score -= 40
    if meta_diffs:
        score -= min(30, len(meta_diffs) * 10)
    if social_crawler_blindspot:
        score -= 10
    if dropped_schemas:
        score -= min(25, len(dropped_schemas) * 15)
    if dropped_internal:
        score -= min(20, len(dropped_internal) * 2)

    score = max(0, score)

    return {
        "url": base_url,
        "health_score": score,
        "robots_danger": robots_danger,
        "social_crawler_blindspot": social_crawler_blindspot,
        "metadata": {
            "ssr": ssr_meta,
            "csr": csr_meta,
            "diffs": meta_diffs
        },
        "social": {
            "ssr": ssr_social,
            "csr": csr_social,
            "diffs": social_diffs,
            "has_blindspot": social_crawler_blindspot
        },
        "schemas": {
            "ssr_count": len(ssr_schemas),
            "csr_count": len(csr_schemas),
            "ssr_types": ssr_types,
            "csr_types": csr_types,
            "dropped_on_hydration": dropped_schemas,
            "injected_on_hydration": injected_schemas
        },
        "links": {
            "ssr_internal_count": len(ssr_int),
            "csr_internal_count": len(csr_int),
            "csr_only_internal": list(csr_only_internal)[:20],
            "csr_only_internal_total": len(csr_only_internal),
            "dropped_internal": list(dropped_internal)[:20],
            "dropped_internal_total": len(dropped_internal)
        },
        "dom_stats": {
            "ssr": ssr_stats,
            "csr": csr_stats,
            "node_bloat": node_bloat,
            "node_bloat_percent": node_bloat_percent
        }
    }
