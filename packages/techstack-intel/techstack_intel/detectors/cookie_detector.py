"""Cookie analysis detector."""

from __future__ import annotations

from techstack_intel.detectors.base import BaseDetector
from techstack_intel.models import DetectedTechnology, DetectionTarget
from techstack_intel.signatures.database import (
    COOKIE_PREFIX_SIGNATURES,
    COOKIE_SIGNATURES,
)


class CookieDetector(BaseDetector):
    name = "cookie_detector"

    async def detect(self, target: DetectionTarget) -> list[DetectedTechnology]:
        results: list[DetectedTechnology] = []
        if not target.cookies:
            return results

        seen: set[str] = set()

        for cookie in target.cookies:
            # Handle both dict and other cookie formats
            if isinstance(cookie, dict):
                name = cookie.get("name", "")
            elif hasattr(cookie, "name"):
                name = cookie.name
            else:
                continue

            if not name:
                continue

            # Exact match
            if name in COOKIE_SIGNATURES:
                sig = COOKIE_SIGNATURES[name]
                key = f"{sig['name']}|{sig['category']}"
                if key not in seen:
                    seen.add(key)
                    results.append(DetectedTechnology(
                        name=sig["name"],
                        category=sig["category"],
                        confidence=sig.get("confidence", 0.8),
                        evidence=[f"cookie: {name}"],
                        website=sig.get("website"),
                    ))
                else:
                    # Add additional cookie as evidence
                    for r in results:
                        if r.name == sig["name"] and r.category == sig["category"]:
                            r.evidence.append(f"cookie: {name}")
                            break

            # Prefix match
            name_lower = name.lower()
            for prefix, sig in COOKIE_PREFIX_SIGNATURES.items():
                if name_lower.startswith(prefix.lower()):
                    key = f"{sig['name']}|{sig['category']}"
                    if key not in seen:
                        seen.add(key)
                        results.append(DetectedTechnology(
                            name=sig["name"],
                            category=sig["category"],
                            confidence=sig.get("confidence", 0.7),
                            evidence=[f"cookie: {name} (prefix: {prefix})"],
                            website=sig.get("website"),
                        ))
                    break

        return results
