"""SSL/TLS certificate analysis detector."""

from __future__ import annotations

from lib.detectors.base import BaseDetector
from lib.models import DetectedTechnology, DetectionTarget
from lib.signatures.database import SSL_ISSUER_MAP


class SSLDetector(BaseDetector):
    name = "ssl_detector"

    async def detect(self, target: DetectionTarget) -> list[DetectedTechnology]:
        results: list[DetectedTechnology] = []

        if not target.ssl_issuer:
            return results

        issuer_lower = target.ssl_issuer.lower()

        for pattern, sig in SSL_ISSUER_MAP.items():
            if pattern in issuer_lower:
                results.append(DetectedTechnology(
                    name=sig["name"],
                    category=sig["category"],
                    subcategory=sig.get("subcategory"),
                    confidence=sig.get("confidence", 0.8),
                    evidence=[f"ssl: issuer = {target.ssl_issuer}"],
                    website=sig.get("website"),
                ))
                break

        # Detect certificate type from subject fields
        org = target.ssl_subject.get("organizationName", "")
        if org:
            # EV certs have org info — signals enterprise
            results.append(DetectedTechnology(
                name="EV/OV SSL Certificate",
                category="SSL / Certificate Authority",
                confidence=0.3,
                evidence=[f"ssl: subject organization = {org}"],
            ))

        return results
