"""Integration tests that scan real websites and validate detection accuracy.

These tests require network access and take 5-15 seconds each.
Run with: pytest packages/techstack-intel/tests/test_integration.py -v -s
"""

import asyncio
import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.analyzer import analyze


# Expected technologies for known sites.
# Only use sites confirmed to reach networkidle quickly with Playwright.
# Complex sites with background polling (e.g. wordpress.org, vercel.com) hang indefinitely.
KNOWN_STACKS = [
    (
        "https://ekas.io",
        ["Next.js", "HubSpot", "Google Workspace", "Google Fonts"],
        ["JavaScript Framework", "Marketing Automation", "Email Provider"],
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("url,expected_techs,expected_categories", KNOWN_STACKS)
async def test_known_site(url, expected_techs, expected_categories):
    """Scan a real website and assert expected technologies and categories are detected."""
    report = await analyze(url)

    detected_names = {t.name for t in report.technologies}
    detected_categories = {t.category for t in report.technologies}

    assert len(report.technologies) > 0, f"No technologies detected for {url}"
    assert report.scan_duration_seconds <= 60, (
        f"Scan took too long: {report.scan_duration_seconds}s"
    )

    for tech in expected_techs:
        assert tech in detected_names, (
            f"{url}: expected '{tech}' not detected. Got: {sorted(detected_names)}"
        )

    for category in expected_categories:
        assert category in detected_categories, (
            f"{url}: expected category '{category}' not found. Got: {sorted(detected_categories)}"
        )
