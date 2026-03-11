"""Favicon hash fingerprinting detector."""

from __future__ import annotations

from lib.detectors.base import BaseDetector
from lib.models import DetectedTechnology, DetectionTarget
from lib.signatures.database import FAVICON_HASH_MAP


class FaviconDetector(BaseDetector):
    name = "favicon_detector"

    async def detect(self, target: DetectionTarget) -> list[DetectedTechnology]:
        results: list[DetectedTechnology] = []

        if not target.favicon_hash:
            return results

        if target.favicon_hash in FAVICON_HASH_MAP:
            sig = FAVICON_HASH_MAP[target.favicon_hash]
            results.append(DetectedTechnology(
                name=sig["name"],
                category=sig["category"],
                confidence=sig.get("confidence", 0.6),
                evidence=[f"favicon hash: {target.favicon_hash}"],
                website=sig.get("website"),
            ))

        return results
