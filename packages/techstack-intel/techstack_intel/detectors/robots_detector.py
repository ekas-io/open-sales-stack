"""robots.txt & sitemap.xml analysis detector."""

from __future__ import annotations

from techstack_intel.detectors.base import BaseDetector
from techstack_intel.models import DetectedTechnology, DetectionTarget
from techstack_intel.signatures.database import ROBOTS_SIGNATURES, SITEMAP_SIGNATURES


class RobotsDetector(BaseDetector):
    name = "robots_detector"

    async def detect(self, target: DetectionTarget) -> list[DetectedTechnology]:
        results: list[DetectedTechnology] = []

        # robots.txt
        if target.robots_txt:
            robots_lower = target.robots_txt.lower()
            for sig in ROBOTS_SIGNATURES:
                if sig["pattern"].lower() in robots_lower:
                    results.append(DetectedTechnology(
                        name=sig["name"],
                        category=sig["category"],
                        confidence=sig.get("confidence", 0.7),
                        evidence=[f"robots.txt contains: {sig['pattern']}"],
                        website=sig.get("website"),
                    ))

        # sitemap.xml
        if target.sitemap_xml:
            sitemap_lower = target.sitemap_xml.lower()
            for sig in SITEMAP_SIGNATURES:
                if sig["pattern"].lower() in sitemap_lower:
                    results.append(DetectedTechnology(
                        name=sig["name"],
                        category=sig["category"],
                        confidence=sig.get("confidence", 0.7),
                        evidence=[f"sitemap.xml contains: {sig['pattern']}"],
                        website=sig.get("website"),
                    ))

        return results
