"""Shared data models for tech stack detection."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class DetectionTarget:
    """All data collected about a target URL, shared across detectors."""

    url: str
    final_url: str
    domain: str

    # From Crawl4AI (headless browser)
    html: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    cookies: list[dict] = field(default_factory=list)
    scripts: list[str] = field(default_factory=list)
    meta_tags: dict[str, str] = field(default_factory=dict)
    inline_scripts: list[str] = field(default_factory=list)
    link_tags: list[str] = field(default_factory=list)

    # From DNS (dnspython)
    mx_records: list[str] = field(default_factory=list)
    txt_records: list[str] = field(default_factory=list)
    cname_records: dict[str, str] = field(default_factory=dict)
    ns_records: list[str] = field(default_factory=list)

    # From SSL (stdlib)
    ssl_issuer: str = ""
    ssl_subject: dict = field(default_factory=dict)
    ssl_san: list[str] = field(default_factory=list)

    # Supplementary fetches
    robots_txt: str | None = None
    sitemap_xml: str | None = None
    favicon_hash: str | None = None


@dataclass
class DetectedTechnology:
    """A single detected technology."""

    name: str
    category: str
    subcategory: str | None = None
    confidence: float = 0.7
    evidence: list[str] = field(default_factory=list)
    version: str | None = None
    website: str | None = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "category": self.category,
            "subcategory": self.subcategory,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "version": self.version,
            "website": self.website,
        }


@dataclass
class TechStackReport:
    """Complete scan report."""

    url: str
    final_url: str
    domain: str
    scan_timestamp: str = ""
    scan_duration_seconds: float = 0.0
    technologies: list[DetectedTechnology] = field(default_factory=list)
    raw_signals: dict = field(default_factory=dict)
    detector_errors: dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        if not self.scan_timestamp:
            self.scan_timestamp = datetime.now(timezone.utc).isoformat()

    def by_category(self) -> dict[str, list[DetectedTechnology]]:
        """Group technologies by category."""
        grouped: dict[str, list[DetectedTechnology]] = {}
        for tech in self.technologies:
            grouped.setdefault(tech.category, []).append(tech)
        return grouped

    def to_dict(self) -> dict:
        result = {
            "url": self.url,
            "final_url": self.final_url,
            "domain": self.domain,
            "scan_timestamp": self.scan_timestamp,
            "scan_duration_seconds": self.scan_duration_seconds,
            "technologies": [t.to_dict() for t in self.technologies],
        }
        if self.detector_errors:
            result["detector_errors"] = self.detector_errors
        return result

    def summary(self) -> str:
        lines = [
            f"Tech Stack Report for {self.domain}",
            f"Scanned: {self.scan_timestamp} ({self.scan_duration_seconds:.1f}s)",
            f"Technologies found: {len(self.technologies)}",
            "",
        ]
        for category, techs in sorted(self.by_category().items()):
            lines.append(f"{category}:")
            for t in sorted(techs, key=lambda x: -x.confidence):
                conf = f"{t.confidence:.0%}"
                ver = f" v{t.version}" if t.version else ""
                lines.append(f"  - {t.name}{ver} ({conf})")
            lines.append("")
        if self.detector_errors:
            lines.append("Detector errors:")
            for name, err in self.detector_errors.items():
                lines.append(f"  - {name}: {err}")
        return "\n".join(lines)
