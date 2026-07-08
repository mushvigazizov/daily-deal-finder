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

print("Premium UI Generator Ready")
print(f"Pages: {len(PAGES)}")
