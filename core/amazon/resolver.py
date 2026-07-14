"""Amazon Identity Resolver — pure decision engine.

No filesystem access. No side effects. No JSON loading.
Receives in-memory Product + Candidates, returns ResolutionResult.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from core.amazon.config import (
    RESOLVER_GUARD_MODE,
    RESOLVER_THRESHOLDS,
    RESOLVER_WEIGHTS,
)

ASIN_PATTERN = re.compile(r"^[A-Z0-9]{10}$")


class ResolutionDecision(str, Enum):
    VERIFIED = "VERIFIED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    REJECTED = "REJECTED"
    CONFLICT = "CONFLICT"
    BLOCKED = "BLOCKED"


@dataclass
class ResolutionResult:
    product_id: str
    decision: ResolutionDecision
    confidence: float = 0.0
    best_candidate: dict[str, Any] | None = None
    score_breakdown: dict[str, float] = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    should_lock: bool = False
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = (
                datetime.now(timezone.utc)
                .replace(microsecond=0)
                .isoformat()
                .replace("+00:00", "Z")
            )


# ── Normalizers ─────────────────────────────────────────────
def _normalise(value: Any) -> str:
    text = str(value or "").lower().strip()
    text = re.sub(r"[^\w\u00e4\u00f6\u00fc\u00df]+", " ", text, flags=re.UNICODE)
    return " ".join(text.split())


def _tokens(value: Any) -> set[str]:
    return {t for t in _normalise(value).split() if len(t) >= 2}


# ── Scoring ────────────────────────────────────────────────
def _overlap(expected: Any, candidate: Any) -> float:
    exp = _tokens(expected)
    cand = _tokens(candidate)
    if not exp or not cand:
        return 0.0
    return len(exp & cand) / len(exp)


def _contains(needle: Any, haystack: Any) -> float:
    n = _normalise(needle)
    h = _normalise(haystack)
    return 1.0 if n and n in h else 0.0


def _score_candidate(product: dict, candidate: dict) -> dict[str, Any]:
    title = _overlap(product.get("title", ""), candidate.get("amazon_product_title", ""))
    brand = max(
        _overlap(product.get("brand", ""), candidate.get("amazon_brand", "")),
        _contains(product.get("brand", ""), candidate.get("amazon_product_title", "")),
    )
    features_text = " ".join(product.get("features") or [])
    cand_specs = " ".join(candidate.get("amazon_key_specs") or [])
    features = _overlap(features_text, f"{candidate.get('amazon_product_title', '')} {cand_specs}")
    model = _contains(candidate.get("amazon_model", ""), candidate.get("amazon_product_title", "")) if candidate.get("amazon_model") else 0.0

    w = RESOLVER_WEIGHTS
    weighted = title * w["TITLE"] + brand * w["BRAND"] + features * w["FEATURES"] + model * w["MODEL"]
    confidence = round(weighted * 100, 2)

    return {
        "asin": candidate.get("asin", ""),
        "amazon_url": candidate.get("amazon_url", ""),
        "amazon_product_title": candidate.get("amazon_product_title", ""),
        "amazon_brand": candidate.get("amazon_brand", ""),
        "amazon_model": candidate.get("amazon_model", ""),
        "confidence": confidence,
        "score_breakdown": {
            "title": round(title * 100, 2),
            "brand": round(brand * 100, 2),
            "features": round(features * 100, 2),
            "model": round(model * 100, 2),
        },
    }


# ── Validation ─────────────────────────────────────────────
def _validate_candidate(candidate: dict, index: int) -> list[str]:
    errors: list[str] = []
    prefix = f"candidate #{index}"
    asin = str(candidate.get("asin", "")).strip().upper()
    if not ASIN_PATTERN.fullmatch(asin):
        errors.append(f"{prefix}: invalid ASIN {asin!r}")
    if not str(candidate.get("amazon_url", "")).strip():
        errors.append(f"{prefix}: missing amazon_url")
    if not str(candidate.get("amazon_product_title", "")).strip():
        errors.append(f"{prefix}: missing amazon_product_title")
    if not str(candidate.get("amazon_brand", "")).strip():
        errors.append(f"{prefix}: missing amazon_brand")
    return errors


# ── Resolver ───────────────────────────────────────────────
class AmazonIdentityResolver:
    """Pure decision engine. No IO."""

    def __init__(self, guard_mode: bool | None = None):
        self._guard = RESOLVER_GUARD_MODE if guard_mode is None else guard_mode

    def resolve(self, product: dict[str, Any], candidates: list[dict[str, Any]]) -> ResolutionResult:
        pid = str(product.get("id", ""))

        # ── BLOCKED: no candidates ──
        if not candidates:
            return ResolutionResult(
                product_id=pid,
                decision=ResolutionDecision.BLOCKED,
                reasons=["cannot resolve without candidates"],
                errors=["no candidates provided"],
            )

        # ── Validate all candidates ──
        all_errors: list[str] = []
        valid: list[dict] = []
        for i, c in enumerate(candidates, 1):
            errs = _validate_candidate(c, i)
            if errs:
                all_errors.extend(errs)
            else:
                valid.append(c)

        # ── BLOCKED: all invalid ──
        if not valid:
            return ResolutionResult(
                product_id=pid,
                decision=ResolutionDecision.BLOCKED,
                reasons=[f"all {len(candidates)} candidates failed validation"],
                errors=all_errors,
            )

        # ── Score and sort ──
        scored = [_score_candidate(product, c) for c in valid]
        scored.sort(key=lambda s: (-s["confidence"], s["asin"]))
        best = scored[0]
        conf = best["confidence"]

        # ── CONFLICT: locked identity mismatch ──
        locked = product.get("identity_locked") is True
        locked_asin = str(product.get("verified_asin", "")).strip().upper()
        if self._guard and locked and locked_asin and best["asin"] != locked_asin:
            return ResolutionResult(
                product_id=pid,
                decision=ResolutionDecision.CONFLICT,
                reasons=[f"locked ASIN {locked_asin} != best candidate {best['asin']}"],
            )

        # ── Decide ──
        thr = RESOLVER_THRESHOLDS
        if conf >= thr["STRONG_MIN"]:
            decision = ResolutionDecision.VERIFIED
            should_lock = True
            reasons = [f"strong match at {conf}% (title {best['score_breakdown']['title']}%, brand {best['score_breakdown']['brand']}%)"]
        elif conf >= thr["MANUAL_MIN"]:
            decision = ResolutionDecision.REVIEW_REQUIRED
            should_lock = False
            reasons = [f"best candidate at {conf}% is below {thr['STRONG_MIN']}% VERIFIED threshold"]
        else:
            decision = ResolutionDecision.REJECTED
            should_lock = False
            reasons = [f"best candidate at {conf}% is below {thr['MANUAL_MIN']}% threshold"]

        return ResolutionResult(
            product_id=pid,
            decision=decision,
            confidence=conf,
            best_candidate=best,
            score_breakdown=best["score_breakdown"],
            reasons=reasons,
            errors=all_errors,
            should_lock=should_lock,
        )
