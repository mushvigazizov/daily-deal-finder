from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def run_step(
    title: str,
    command: list[str],
) -> int:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)
    print("Command:", " ".join(command))
    print()

    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        check=False,
    )

    if result.returncode != 0:
        print()
        print(f"WORKFLOW STOPPED: {title}")
        print(f"Exit code       : {result.returncode}")
        return result.returncode

    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the complete safe Amazon product identity workflow."
        )
    )

    parser.add_argument(
        "--write",
        action="store_true",
        help=(
            "Apply valid locked identities to products.json. "
            "Without this flag the workflow remains read-only."
        ),
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    python = sys.executable

    print("=" * 78)
    print("AMAZON PRODUCT IDENTITY WORKFLOW")
    print("=" * 78)
    print(
        "Mode : "
        + ("WRITE" if args.write else "DRY RUN")
    )

    steps: list[tuple[str, list[str]]] = [
        (
            "STEP 1 — CURRENT PRODUCT IDENTITY AUDIT",
            [
                python,
                "scripts/amazon/audit_product_identity.py",
            ],
        ),
        (
            "STEP 2 — LOCKED IDENTITY INTEGRITY CHECK",
            [
                python,
                "scripts/amazon/apply_locked_product_identities.py",
            ],
        ),
    ]

    if args.write:
        steps.append(
            (
                "STEP 3 — APPLY LOCKED IDENTITIES",
                [
                    python,
                    "scripts/amazon/apply_locked_product_identities.py",
                    "--write",
                ],
            )
        )
    else:
        steps.append(
            (
                "STEP 3 — WRITE PHASE",
                [
                    python,
                    "-c",
                    (
                        "print('Write phase skipped: "
                        "workflow is running in dry-run mode.')"
                    ),
                ],
            )
        )

    steps.extend(
        [
            (
                "STEP 4 — FINAL PRODUCT IDENTITY AUDIT",
                [
                    python,
                    "scripts/amazon/audit_product_identity.py",
                ],
            ),
        ]
    )

    for title, command in steps:
        exit_code = run_step(title, command)

        if exit_code != 0:
            return exit_code

    print()
    print("=" * 78)
    print("AMAZON PRODUCT IDENTITY WORKFLOW COMPLETED")
    print("=" * 78)
    print(
        "Result : "
        + (
            "SAFE WRITE WORKFLOW PASSED"
            if args.write
            else "SAFE DRY RUN PASSED"
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
