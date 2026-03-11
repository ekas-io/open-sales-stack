"""HTTP response header analysis detector."""

from __future__ import annotations

import re

from lib.detectors.base import BaseDetector
from lib.models import DetectedTechnology, DetectionTarget
from lib.signatures.database import (
    HEADER_POWERED_BY_MAP,
    HEADER_PREFIX_SIGNATURES,
    HEADER_PRESENCE_SIGNATURES,
    HEADER_SERVER_MAP,
    HEADER_VIA_MAP,
    SECURITY_HEADERS,
)


class HeaderDetector(BaseDetector):
    name = "header_detector"

    async def detect(self, target: DetectionTarget) -> list[DetectedTechnology]:
        results: list[DetectedTechnology] = []
        headers = target.headers
        if not headers:
            return results

        # Server header
        server = headers.get("server", "")
        if server:
            server_lower = server.lower()
            for key, sig in HEADER_SERVER_MAP.items():
                if key in server_lower:
                    version = None
                    ver_match = re.search(r"[\d]+(?:\.[\d]+)+", server)
                    if ver_match:
                        version = ver_match.group(0)
                    results.append(DetectedTechnology(
                        name=sig["name"],
                        category=sig["category"],
                        confidence=0.9,
                        evidence=[f"header: Server: {server}"],
                        version=version,
                        website=sig.get("website"),
                    ))
                    break

        # X-Powered-By
        powered_by = headers.get("x-powered-by", "")
        if powered_by:
            pb_lower = powered_by.lower()
            for key, sig in HEADER_POWERED_BY_MAP.items():
                if key in pb_lower:
                    version = None
                    ver_match = re.search(r"[\d]+(?:\.[\d]+)+", powered_by)
                    if ver_match:
                        version = ver_match.group(0)
                    results.append(DetectedTechnology(
                        name=sig["name"],
                        category=sig["category"],
                        confidence=0.9,
                        evidence=[f"header: X-Powered-By: {powered_by}"],
                        version=version,
                        website=sig.get("website"),
                    ))
                    break

        # X-Generator
        generator = headers.get("x-generator", "")
        if generator:
            results.append(DetectedTechnology(
                name=generator.split("/")[0].strip(),
                category="CMS / Website Builder",
                confidence=0.9,
                evidence=[f"header: X-Generator: {generator}"],
            ))

        # Presence-based headers
        for sig in HEADER_PRESENCE_SIGNATURES:
            if sig["header"] in headers:
                results.append(DetectedTechnology(
                    name=sig["name"],
                    category=sig["category"],
                    confidence=sig["confidence"],
                    evidence=[f"header: {sig['header']} present"],
                    website=sig.get("website"),
                ))

        # Prefix-based headers
        for sig in HEADER_PREFIX_SIGNATURES:
            for hdr_name in headers:
                if hdr_name.startswith(sig["prefix"]):
                    results.append(DetectedTechnology(
                        name=sig["name"],
                        category=sig["category"],
                        confidence=sig["confidence"],
                        evidence=[f"header: {hdr_name} present"],
                        website=sig.get("website"),
                    ))
                    break

        # Via header
        via = headers.get("via", "")
        if via:
            via_lower = via.lower()
            for key, sig in HEADER_VIA_MAP.items():
                if key in via_lower:
                    results.append(DetectedTechnology(
                        name=sig["name"],
                        category=sig["category"],
                        confidence=0.8,
                        evidence=[f"header: Via: {via}"],
                        website=sig.get("website"),
                    ))

        # Security headers (posture signals)
        for sig in SECURITY_HEADERS:
            if sig["header"] in headers:
                results.append(DetectedTechnology(
                    name=sig["name"],
                    category=sig["category"],
                    confidence=0.3,
                    evidence=[f"header: {sig['header']} present"],
                ))

        # CSP header — parse for third-party domains
        csp = headers.get("content-security-policy", "")
        if csp:
            # Extract domain-like patterns from CSP
            domains_in_csp = re.findall(r"[\w.-]+\.(?:com|io|net|org|co)", csp)
            for domain in set(domains_in_csp):
                domain_lower = domain.lower()
                if "google" in domain_lower and "analytics" in domain_lower:
                    results.append(DetectedTechnology(
                        name="Google Analytics",
                        category="Analytics",
                        confidence=0.5,
                        evidence=[f"header: CSP allows {domain}"],
                        website="https://analytics.google.com",
                    ))
                elif "cloudflare" in domain_lower:
                    results.append(DetectedTechnology(
                        name="Cloudflare",
                        category="CDN",
                        confidence=0.5,
                        evidence=[f"header: CSP allows {domain}"],
                        website="https://cloudflare.com",
                    ))

        return results
