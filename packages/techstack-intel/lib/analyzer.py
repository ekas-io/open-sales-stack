"""Main orchestrator — analyze(url) function."""

from __future__ import annotations

import asyncio
import logging
import time

from lib.detectors.base import BaseDetector
from lib.detectors.cookie_detector import CookieDetector
from lib.detectors.dns_detector import DNSDetector
from lib.detectors.favicon_detector import FaviconDetector
from lib.detectors.header_detector import HeaderDetector
from lib.detectors.html_detector import HTMLDetector
from lib.detectors.robots_detector import RobotsDetector
from lib.detectors.ssl_detector import SSLDetector
from lib.models import DetectedTechnology, TechStackReport
from lib.target_builder import build_target

logger = logging.getLogger("techstack-intel.analyzer")

# Registry of all detectors — add new detectors here
ALL_DETECTORS: list[BaseDetector] = [
    HeaderDetector(),
    HTMLDetector(),
    DNSDetector(),
    SSLDetector(),
    RobotsDetector(),
    CookieDetector(),
    FaviconDetector(),
]


def _merge_technologies(all_results: list[DetectedTechnology]) -> list[DetectedTechnology]:
    """Deduplicate and merge technologies detected by multiple detectors.

    When the same technology is detected by multiple detectors:
    - Merge evidence lists
    - Take the highest confidence score (or boost if multiple independent signals)
    - Keep version if any detector found one
    """
    merged: dict[str, DetectedTechnology] = {}

    for tech in all_results:
        # Key by name + category for deduplication
        key = f"{tech.name}|{tech.category}"

        if key not in merged:
            merged[key] = DetectedTechnology(
                name=tech.name,
                category=tech.category,
                subcategory=tech.subcategory,
                confidence=tech.confidence,
                evidence=list(tech.evidence),
                version=tech.version,
                website=tech.website,
            )
        else:
            existing = merged[key]
            # Merge evidence
            for e in tech.evidence:
                if e not in existing.evidence:
                    existing.evidence.append(e)
            # Boost confidence if multiple independent signals
            if tech.confidence > 0.3 and existing.confidence > 0.3:
                existing.confidence = min(1.0, max(existing.confidence, tech.confidence) + 0.05)
            else:
                existing.confidence = max(existing.confidence, tech.confidence)
            # Keep version if found
            if tech.version and not existing.version:
                existing.version = tech.version
            # Keep subcategory if found
            if tech.subcategory and not existing.subcategory:
                existing.subcategory = tech.subcategory
            # Keep website if found
            if tech.website and not existing.website:
                existing.website = tech.website

    # Filter out low-confidence results
    return [
        tech for tech in merged.values()
        if tech.confidence >= 0.3
    ]


async def _run_detectors(target) -> tuple[list[DetectedTechnology], dict[str, str]]:
    """Run all detectors in parallel. Returns (flat tech list, error dict)."""
    detector_errors: dict[str, str] = {}

    async def _run_one(detector: BaseDetector) -> list[DetectedTechnology]:
        try:
            return await detector.detect(target)
        except Exception as e:
            logger.error("Detector %s failed: %s", detector.name, e)
            detector_errors[detector.name] = str(e)
            return []

    results = await asyncio.gather(*[_run_one(d) for d in ALL_DETECTORS])
    all_techs: list[DetectedTechnology] = [t for result_list in results for t in result_list]
    return all_techs, detector_errors


def _build_report(target, merged, elapsed, detector_errors) -> TechStackReport:
    """Assemble a TechStackReport from merged detection results."""
    return TechStackReport(
        url=target.url,
        final_url=target.final_url,
        domain=target.domain,
        scan_duration_seconds=round(elapsed, 2),
        technologies=merged,
        detector_errors=detector_errors,
        raw_signals={
            "headers": dict(target.headers) if target.headers else {},
            "mx_records": target.mx_records,
            "ns_records": target.ns_records,
            "txt_records": target.txt_records,
            "cname_records": target.cname_records,
            "ssl_issuer": target.ssl_issuer,
            "favicon_hash": target.favicon_hash,
        },
    )


async def analyze(url: str) -> TechStackReport:
    """Analyze a URL and return a comprehensive tech stack report."""
    start_time = time.monotonic()

    logger.info("Building detection target for %s", url)
    target = await build_target(url)

    logger.info("Running %d detectors", len(ALL_DETECTORS))
    all_techs, detector_errors = await _run_detectors(target)

    merged = _merge_technologies(all_techs)
    merged.sort(key=lambda t: (-t.confidence, t.name))

    elapsed = time.monotonic() - start_time
    report = _build_report(target, merged, elapsed, detector_errors)

    logger.info("Analysis complete for %s: %d technologies in %.1fs", url, len(merged), elapsed)
    return report
