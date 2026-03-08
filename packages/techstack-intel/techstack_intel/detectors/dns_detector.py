"""DNS record analysis detector."""

from __future__ import annotations

from techstack_intel.detectors.base import BaseDetector
from techstack_intel.models import DetectedTechnology, DetectionTarget
from techstack_intel.signatures.database import (
    CNAME_TARGET_MAP,
    MX_PROVIDER_MAP,
    NS_PROVIDER_MAP,
    TXT_SPF_MAP,
    TXT_VERIFICATION_MAP,
)


class DNSDetector(BaseDetector):
    name = "dns_detector"

    async def detect(self, target: DetectionTarget) -> list[DetectedTechnology]:
        results: list[DetectedTechnology] = []

        # MX records -> Email provider
        for mx in target.mx_records:
            mx_lower = mx.lower()
            for pattern, sig in MX_PROVIDER_MAP.items():
                if pattern in mx_lower:
                    results.append(DetectedTechnology(
                        name=sig["name"],
                        category=sig["category"],
                        subcategory=sig.get("subcategory"),
                        confidence=1.0,
                        evidence=[f"dns: MX -> {mx}"],
                        website=sig.get("website"),
                    ))
                    break

        # TXT records -> SPF includes and domain verifications
        for txt in target.txt_records:
            txt_lower = txt.lower()

            # SPF include patterns
            if "v=spf1" in txt_lower or "include:" in txt_lower:
                for pattern, sig in TXT_SPF_MAP.items():
                    if pattern.lower() in txt_lower:
                        results.append(DetectedTechnology(
                            name=sig["name"],
                            category=sig["category"],
                            subcategory=sig.get("subcategory"),
                            confidence=0.8,
                            evidence=[f"dns: TXT SPF includes {pattern}"],
                            website=sig.get("website"),
                        ))

            # Domain verification strings
            for prefix, sig in TXT_VERIFICATION_MAP.items():
                if txt.startswith(prefix) or txt_lower.startswith(prefix.lower()):
                    results.append(DetectedTechnology(
                        name=sig["name"],
                        category=sig["category"],
                        subcategory=sig.get("subcategory"),
                        confidence=sig.get("confidence", 0.5),
                        evidence=[f"dns: TXT verification record for {sig['name']}"],
                        website=sig.get("website"),
                    ))

        # CNAME records -> Hosted services
        for subdomain, cname_target in target.cname_records.items():
            cname_lower = cname_target.lower()
            for pattern, sig in CNAME_TARGET_MAP.items():
                if pattern in cname_lower:
                    results.append(DetectedTechnology(
                        name=sig["name"],
                        category=sig["category"],
                        confidence=0.9,
                        evidence=[f"dns: CNAME {subdomain} -> {cname_target}"],
                        website=sig.get("website"),
                    ))
                    break

        # NS records -> DNS provider
        for ns in target.ns_records:
            ns_lower = ns.lower()
            for pattern, sig in NS_PROVIDER_MAP.items():
                if pattern in ns_lower:
                    results.append(DetectedTechnology(
                        name=sig["name"],
                        category=sig["category"],
                        confidence=0.9,
                        evidence=[f"dns: NS -> {ns}"],
                        website=sig.get("website"),
                    ))
                    break

        return results
