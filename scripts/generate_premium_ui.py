"""
Daily Deal Finder
Premium UI Generator

This script will generate and synchronize
shared UI components across all HTML pages.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PAGES = [
    "index.html",
    "about.html",
    "contact.html",
    "privacy.html",
    "terms.html",
    "impressum.html",
    "affiliate-disclosure.html",
    "product.html",
]


STYLE_BLOCK = """  <link rel="stylesheet" href="/styles.css" />
  <link rel="stylesheet" href="/styles/base.css" />
  <link rel="stylesheet" href="/styles/header.css" />
  <link rel="stylesheet" href="/styles/footer.css" />"""

def sync_styles():
    for page in PAGES:
        file_path = ROOT / page
        html = file_path.read_text(encoding="utf-8")

        if 'href="/styles/base.css"' not in html:
            html = html.replace(
                '  <link rel="stylesheet" href="/styles.css" />',
                STYLE_BLOCK
            )

        file_path.write_text(html, encoding="utf-8")

    print("Synchronized premium styles")

print("Premium UI Generator Ready")
print(f"Pages: {len(PAGES)}")


if __name__ == "__main__":
    sync_styles()
