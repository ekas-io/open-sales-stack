"""Main orchestrator — analyze(url) function."""

from __future__ import annotations

import asyncio
import logging
import time

from techstack_intel.detectors.base import BaseDetector
from techstack_intel.detectors.cookie_detector import CookieDetector
from techstack_intel.detectors.dns_detector import DNSDetector
from techstack_intel.detectors.favicon_detector import FaviconDetector
from techstack_intel.detectors.header_detector import HeaderDetector
from techstack_intel.detectors.html_detector import HTMLDetector
from techstack_intel.detectors.robots_detector import RobotsDetector
from techstack_intel.detectors.ssl_detector import SSLDetector
from techstack_intel.models import DetectedTechnology, TechStackReport
from techstack_intel.target_builder import build_target

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


async def analyze(url: str) -> TechStackReport:
    """Analyze a URL and return a comprehensive tech stack report.

    1. Builds a DetectionTarget (page fetch, DNS, SSL, robots in parallel)
    2. Runs all detectors in parallel against the target
    3. Merges and deduplicates results
    4. Returns a TechStackReport
    """
    start_time = time.monotonic()

    # Step 1: Build the detection target
    logger.info("Building detection target for %s", url)
    target = await build_target(url)

    # Step 2: Run all detectors in parallel
    logger.info("Running %d detectors", len(ALL_DETECTORS))
    detector_errors: dict[str, str] = {}

    async def _run_detector(detector: BaseDetector) -> list[DetectedTechnology]:
        try:
            return await detector.detect(target)
        except Exception as e:
            logger.error("Detector %s failed: %s", detector.name, e)
            detector_errors[detector.name] = str(e)
            return []

    detector_tasks = [_run_detector(d) for d in ALL_DETECTORS]
    all_detector_results = await asyncio.gather(*detector_tasks)

    # Step 3: Flatten and merge results
    all_techs: list[DetectedTechnology] = []
    for result_list in all_detector_results:
        all_techs.extend(result_list)

    merged = _merge_technologies(all_techs)

    # Sort by confidence descending, then by name
    merged.sort(key=lambda t: (-t.confidence, t.name))

    elapsed = time.monotonic() - start_time

    # Step 4: Build report
    report = TechStackReport(
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

    logger.info(
        "Analysis complete for %s: %d technologies found in %.1fs",
        url, len(merged), elapsed,
    )

    return report
