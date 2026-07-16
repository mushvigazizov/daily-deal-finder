#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PRODUCTS_PATH = ROOT / "data/products.json"
REGISTRY_PATH = ROOT / "scripts/importers/asin_import_template.json"
LIVE_PRODUCTS_URL = "https://daily-deal-finder.com/data/products.json"


def run(
    command: list[str],
    *,
    check: bool = True,
    capture: bool = False,
) -> subprocess.CompletedProcess[str]:
    print("\n$", " ".join(command))

    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=capture,
    )

    if capture:
        if result.stdout:
            print(result.stdout.rstrip())
        if result.stderr:
            print(result.stderr.rstrip(), file=sys.stderr)

    if check and result.returncode != 0:
        raise RuntimeError(
            f"Command failed with exit code {result.returncode}: "
            f"{' '.join(command)}"
        )

    return result


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def find_product(product_id: str) -> dict[str, Any]:
    payload = load_json(PRODUCTS_PATH)
    products = payload.get("products", payload)

    product = next(
        (item for item in products if item.get("id") == product_id),
        None,
    )

    if product is None:
        raise RuntimeError(f"Product not found: {product_id}")

    return product


def find_registry_record(product_id: str) -> dict[str, Any]:
    registry = load_json(REGISTRY_PATH)

    record = next(
        (item for item in registry if item.get("id") == product_id),
        None,
    )

    if record is None:
        raise RuntimeError(
            f"{product_id} is missing from {REGISTRY_PATH.relative_to(ROOT)}"
        )

    return record


def validate_asin(value: str) -> str:
    asin = value.strip().upper()

    if not re.fullmatch(r"[A-Z0-9]{10}", asin):
        raise RuntimeError(f"Invalid ASIN: {value!r}")

    return asin


def validate_registry(
    product_id: str,
    expected_asin: str,
) -> None:
    record = find_registry_record(product_id)

    required_fields = [
        "verified_asin",
        "verified_amazon_url",
        "amazon_product_title",
        "amazon_brand",
        "amazon_model",
        "amazon_key_specs",
        "verification_status",
        "verification_source",
    ]

    missing = [
        field
        for field in required_fields
        if not record.get(field)
    ]

    if missing:
        raise RuntimeError(
            "Registry record is incomplete: " + ", ".join(missing)
        )

    registry_asin = validate_asin(str(record["verified_asin"]))

    if registry_asin != expected_asin:
        raise RuntimeError(
            f"Registry ASIN mismatch: {registry_asin} != {expected_asin}"
        )

    expected_url = f"https://www.amazon.de/dp/{expected_asin}"

    if record.get("verified_amazon_url") != expected_url:
        raise RuntimeError(
            "Registry Amazon URL must be canonical: "
            f"{expected_url}"
        )

    if record.get("verification_status") != "verified":
        raise RuntimeError(
            "Registry verification_status must be verified"
        )


def validate_local_product(
    product_id: str,
    expected_asin: str,
) -> dict[str, Any]:
    product = find_product(product_id)
    expected_url = f"https://www.amazon.de/dp/{expected_asin}"

    expected = {
        "verified_asin": expected_asin,
        "verified_amazon_url": expected_url,
        "verification_status": "verified",
        "amazon_link_type": "product",
        "identity_locked": True,
    }

    errors: list[str] = []

    for field, expected_value in expected.items():
        actual = product.get(field)

        if actual != expected_value:
            errors.append(
                f"{field}: expected {expected_value!r}, got {actual!r}"
            )

    if errors:
        raise RuntimeError(
            "Local product verification failed:\n- "
            + "\n- ".join(errors)
        )

    if not product.get("identity_hash"):
        raise RuntimeError("Local product is missing identity_hash")

    return product


def related_paths(product_id: str) -> list[Path]:
    candidates = [
        PRODUCTS_PATH,
        REGISTRY_PATH,
        ROOT / f"data/content/{product_id}.de.json",
        ROOT / f"data/content/{product_id}.en.json",
        ROOT / f"data/state/{product_id}.json",
        ROOT / f"data/amazon_candidates/{product_id}.json",
        ROOT / f"data/verified_identities/{product_id}.json",
        ROOT / "data/pinterest_content.json",
        ROOT / "data/pinterest_prompts.json",
        ROOT / f"assets/products/{product_id}.webp",
    ]

    return [path for path in candidates if path.exists()]


def stage_related_files(product_id: str) -> list[str]:
    paths = related_paths(product_id)
    relative_paths = [str(path.relative_to(ROOT)) for path in paths]

    run(["git", "add", "--", *relative_paths])
    run(["git", "diff", "--cached", "--check"])

    staged = run(
        ["git", "diff", "--cached", "--name-only"],
        capture=True,
    ).stdout.splitlines()

    unrelated = [
        path for path in staged
        if path not in relative_paths
    ]

    if unrelated:
        raise RuntimeError(
            "Unrelated staged files detected:\n- "
            + "\n- ".join(unrelated)
        )

    if not staged:
        raise RuntimeError("No related changes are staged")

    print("\nStaged files:")
    for path in staged:
        print(f"  - {path}")

    return staged


def get_head() -> str:
    return run(
        ["git", "rev-parse", "HEAD"],
        capture=True,
    ).stdout.strip()


def confirm_origin_contains(commit_hash: str) -> None:
    run(["git", "fetch", "origin", "main"])

    remote_head = run(
        ["git", "rev-parse", "origin/main"],
        capture=True,
    ).stdout.strip()

    if remote_head != commit_hash:
        raise RuntimeError(
            f"Push verification failed: origin/main={remote_head}, "
            f"local={commit_hash}"
        )


def read_live_product(
    product_id: str,
) -> dict[str, Any]:
    cache_buster = urllib.parse.urlencode(
        {"check": int(time.time())}
    )
    url = f"{LIVE_PRODUCTS_URL}?{cache_buster}"

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "DailyDealFinderDeploymentVerifier/1.0",
            "Cache-Control": "no-cache",
        },
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))

    products = payload.get("products", payload)

    product = next(
        (item for item in products if item.get("id") == product_id),
        None,
    )

    if product is None:
        raise RuntimeError(
            f"{product_id} was not found on the live website"
        )

    return product


def wait_for_live_deployment(
    product_id: str,
    asin: str,
    attempts: int = 18,
    delay: int = 10,
) -> dict[str, Any]:
    expected_url = f"https://www.amazon.de/dp/{asin}"

    for attempt in range(1, attempts + 1):
        print(
            f"\nLive deployment check {attempt}/{attempts}..."
        )

        try:
            product = read_live_product(product_id)

            passed = (
                product.get("verified_asin") == asin
                and product.get("verified_amazon_url") == expected_url
                and product.get("verification_status") == "verified"
                and product.get("amazon_link_type") == "product"
                and product.get("identity_locked") is True
            )

            if passed:
                return product

            print(
                "Live version is still old:",
                {
                    "title": product.get("title"),
                    "verified_asin": product.get("verified_asin"),
                    "verification_status": product.get(
                        "verification_status"
                    ),
                    "identity_locked": product.get("identity_locked"),
                },
            )
        except Exception as exc:
            print(f"Live check warning: {exc}")

        time.sleep(delay)

    raise RuntimeError(
        "Netlify deployment was not confirmed within the timeout"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Finalize, test, commit, push and verify one already-reviewed "
            "Amazon product identity."
        )
    )
    parser.add_argument("--product-id", required=True)
    parser.add_argument("--asin", required=True)
    parser.add_argument(
        "--commit-message",
        default=None,
    )
    parser.add_argument(
        "--deploy",
        action="store_true",
        help="Commit, push and verify the live website.",
    )

    args = parser.parse_args()

    product_id = args.product_id.strip()
    asin = validate_asin(args.asin)

    if not re.fullmatch(r"camp-\d{3}", product_id):
        raise RuntimeError(
            "Product ID must look like camp-001"
        )

    print("=" * 78)
    print("AUTOMATED VERIFIED PRODUCT PIPELINE")
    print("=" * 78)
    print("Product ID :", product_id)
    print("ASIN       :", asin)
    print("Mode       :", "DEPLOY" if args.deploy else "DIAGNOSTIC")
    print("=" * 78)

    validate_registry(product_id, asin)
    print("[PASS] Registry identity")

    run([
        sys.executable,
        "scripts/amazon/lock_product_identity.py",
        "--product-id",
        product_id,
        "--write",
    ])

    run([
        sys.executable,
        "scripts/amazon/apply_locked_product_identities.py",
        "--write",
    ])

    validate_local_product(product_id, asin)
    print("[PASS] Local Amazon button conditions")

    run([
        sys.executable,
        "scripts/amazon/audit_product_identity.py",
    ])

    run([
        sys.executable,
        "scripts/amazon/guard_locked_product_identities.py",
    ])

    run([
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        "tests",
        "-v",
    ])

    print("\n[PASS] Audit, guard and tests")

    if not args.deploy:
        print("\nDiagnostic completed. No commit or push was performed.")
        return 0

    previous_head = get_head()
    stage_related_files(product_id)

    commit_message = (
        args.commit_message
        or f"Finalize verified {product_id} product replacement"
    )

    run(["git", "commit", "-m", commit_message])

    new_head = get_head()

    if new_head == previous_head:
        raise RuntimeError("Git commit did not create a new commit")

    run(["git", "push", "origin", "main"])
    confirm_origin_contains(new_head)

    print(f"\n[PASS] Real commit created and pushed: {new_head}")

    live_product = wait_for_live_deployment(
        product_id,
        asin,
    )

    print("\n" + "=" * 78)
    print("LIVE DEPLOYMENT CONFIRMED")
    print("=" * 78)
    print("Title      :", live_product.get("title"))
    print("ASIN       :", live_product.get("verified_asin"))
    print("URL        :", live_product.get("verified_amazon_url"))
    print("Status     :", live_product.get("verification_status"))
    print("Locked     :", live_product.get("identity_locked"))
    print("Commit     :", new_head)
    print("=" * 78)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
