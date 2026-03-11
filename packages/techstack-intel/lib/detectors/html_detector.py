"""HTML / DOM analysis detector."""

from __future__ import annotations

import re

from lib.detectors.base import BaseDetector
from lib.models import DetectedTechnology, DetectionTarget
from lib.signatures.database import (
    ALL_HTML_SIGNATURES,
    CMS_HTML_SIGNATURES,
    META_GENERATOR_MAP,
)
from lib.utils.helpers import extract_version_from_url


class HTMLDetector(BaseDetector):
    name = "html_detector"

    async def detect(self, target: DetectionTarget) -> list[DetectedTechnology]:
        results: list[DetectedTechnology] = []
        if not target.html:
            return results

        # Combine all searchable text
        html_lower = target.html.lower()
        all_scripts = " ".join(target.scripts).lower()
        all_inline = " ".join(target.inline_scripts).lower()
        all_links = " ".join(target.link_tags).lower()
        searchable = f"{html_lower} {all_scripts} {all_inline} {all_links}"

        # Check meta generator tag
        generator = target.meta_tags.get("generator", "")
        if generator:
            gen_lower = generator.lower()
            for key, sig in META_GENERATOR_MAP.items():
                if key in gen_lower:
                    version = None
                    ver_match = re.search(r"[\d]+(?:\.[\d]+)+", generator)
                    if ver_match:
                        version = ver_match.group(0)
                    results.append(DetectedTechnology(
                        name=sig["name"],
                        category=sig["category"],
                        confidence=1.0,
                        evidence=[f'meta generator: "{generator}"'],
                        version=version,
                        website=sig.get("website"),
                    ))

        # Scan all signature groups against the searchable text
        seen: set[str] = set()
        for sig_list in ALL_HTML_SIGNATURES:
            for sig in sig_list:
                pattern = sig["pattern"].lower()
                if pattern in searchable:
                    key = f"{sig['name']}|{sig['category']}"
                    if key not in seen:
                        seen.add(key)

                        # Build evidence — find where we matched
                        evidence_parts = []
                        if pattern in all_scripts:
                            evidence_parts.append(f"script src contains: {sig['pattern']}")
                        if pattern in all_inline:
                            evidence_parts.append(f"inline script contains: {sig['pattern']}")
                        if pattern in html_lower:
                            evidence_parts.append(f"HTML contains: {sig['pattern']}")
                        if pattern in all_links:
                            evidence_parts.append(f"link href contains: {sig['pattern']}")
                        if not evidence_parts:
                            evidence_parts.append(f"pattern found: {sig['pattern']}")

                        # Try to extract version from script URLs
                        version = None
                        for script_url in target.scripts:
                            if pattern in script_url.lower():
                                version = extract_version_from_url(
                                    script_url, sig["name"].lower().split()[0]
                                )
                                if version:
                                    break

                        results.append(DetectedTechnology(
                            name=sig["name"],
                            category=sig["category"],
                            subcategory=sig.get("subcategory"),
                            confidence=sig.get("confidence", 0.7),
                            evidence=evidence_parts,
                            version=version,
                            website=sig.get("website"),
                        ))
                    else:
                        # Already seen — add more evidence to existing
                        for r in results:
                            if r.name == sig["name"] and r.category == sig["category"]:
                                new_evidence = f"also matched: {sig['pattern']}"
                                if new_evidence not in r.evidence:
                                    r.evidence.append(new_evidence)
                                # Boost confidence if corroborated
                                r.confidence = max(r.confidence, sig.get("confidence", 0.7))
                                break

        # Detect Angular via ng-version attribute
        ng_version_match = re.search(r'ng-version="([\d.]+)"', target.html)
        if ng_version_match:
            key = "Angular|JavaScript Framework"
            if key not in seen:
                results.append(DetectedTechnology(
                    name="Angular",
                    category="JavaScript Framework",
                    confidence=1.0,
                    evidence=[f"ng-version attribute: {ng_version_match.group(1)}"],
                    version=ng_version_match.group(1),
                    website="https://angular.io",
                ))

        # Detect Next.js version from __NEXT_DATA__
        next_data_match = re.search(
            r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.+?)</script>',
            target.html,
            re.DOTALL,
        )
        if next_data_match:
            import json
            try:
                next_data = json.loads(next_data_match.group(1))
                build_id = next_data.get("buildId", "")
                # Version might be in runtimeConfig or other fields
                for r in results:
                    if r.name == "Next.js" and not r.version:
                        runtime = next_data.get("runtimeConfig", {})
                        if isinstance(runtime, dict):
                            ver = runtime.get("version") or runtime.get("nextVersion")
                            if ver:
                                r.version = str(ver)
            except (json.JSONDecodeError, AttributeError):
                pass

        return results
