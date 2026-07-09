#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from datetime import datetime, UTC
from xml.sax.saxutils import escape
from core.products import load_products

ROOT = Path(__file__).resolve().parents[1]
SITE_URL = "https://daily-deal-finder.com"

STATIC_PAGES = [
    "",
    "about.html",
    "contact.html",
    "privacy.html",
    "terms.html",
    "impressum.html",
    "affiliate-disclosure.html",
]

def iso_now():
    return datetime.now(UTC).date().isoformat()

def product_url(product):
    product_id = product.get("id")
    if not product_id:
        return None
    return f"product.html?id={product_id}"

def make_url_entry(loc, priority="0.7", changefreq="weekly"):
    return f"""  <url>
    <loc>{escape(SITE_URL + "/" + loc)}</loc>
    <lastmod>{iso_now()}</lastmod>
    <changefreq>{changefreq}</changefreq>
    <priority>{priority}</priority>
  </url>"""

def generate_sitemap():
    products = load_products()
    entries = []

    for page in STATIC_PAGES:
        priority = "1.0" if page == "" else "0.6"
        entries.append(make_url_entry(page, priority=priority))

    for product in products:
        url = product_url(product)
        if url:
            entries.append(make_url_entry(url, priority="0.8"))

    sitemap = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
""" + "\n".join(entries) + """
</urlset>
"""

    (ROOT / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    return len(entries)

def generate_robots():
    robots = f"""User-agent: *
Allow: /

Sitemap: {SITE_URL}/sitemap.xml
"""
    (ROOT / "robots.txt").write_text(robots, encoding="utf-8")

def main():
    count = generate_sitemap()
    generate_robots()

    print("=" * 70)
    print("SEO FILE GENERATOR")
    print("=" * 70)
    print(f"URLs generated: {count}")
    print("Files: sitemap.xml, robots.txt")
    print("Status: PASS")

if __name__ == "__main__":
    main()
