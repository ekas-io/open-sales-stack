"""Integration tests that scan real websites and validate detection accuracy.

These tests require network access and take 5-15 seconds each.
Run with: python tests/test_integration.py
"""

import asyncio
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from techstack_intel import analyze


# Expected technologies for known sites
KNOWN_STACKS = {
    "https://ekas.io": {
        "expected": ["Next.js", "HubSpot", "Google Workspace", "Google Fonts"],
        "expected_categories": ["JavaScript Framework", "Marketing Automation", "Email Provider"],
    },
    "https://vercel.com": {
        "expected": ["Next.js"],
        "expected_categories": ["JavaScript Framework"],
    },
    "https://stripe.com": {
        "expected": ["Next.js", "Nginx"],
        "expected_categories": ["JavaScript Framework", "Web Server", "DNS Provider"],
    },
}


async def test_site(url: str, expectations: dict) -> tuple[bool, list[str]]:
    """Test a single site against expectations."""
    errors = []
    try:
        report = await analyze(url)
    except Exception as e:
        return False, [f"Scan failed: {e}"]

    detected_names = {t.name for t in report.technologies}
    detected_categories = {t.category for t in report.technologies}

    # Check expected technologies
    for expected in expectations.get("expected", []):
        if expected not in detected_names:
            errors.append(f"Expected '{expected}' not detected")

    # Check expected categories
    for expected_cat in expectations.get("expected_categories", []):
        if expected_cat not in detected_categories:
            errors.append(f"Expected category '{expected_cat}' not found")

    # Sanity checks
    if len(report.technologies) == 0:
        errors.append("No technologies detected at all")

    if report.scan_duration_seconds > 60:
        errors.append(f"Scan took too long: {report.scan_duration_seconds}s")

    return len(errors) == 0, errors


async def run_integration_tests():
    """Run integration tests against known sites."""
    total = 0
    passed = 0
    failed = 0
    all_errors: list[tuple[str, list[str]]] = []

    for url, expectations in KNOWN_STACKS.items():
        total += 1
        print(f"\nTesting: {url}")
        start = time.monotonic()
        success, errors = await test_site(url, expectations)
        elapsed = time.monotonic() - start

        if success:
            passed += 1
            print(f"  PASS ({elapsed:.1f}s)")
        else:
            failed += 1
            all_errors.append((url, errors))
            for err in errors:
                print(f"  FAIL: {err}")
            print(f"  ({elapsed:.1f}s)")

    print(f"\n{'='*60}")
    print(f"Integration Results: {passed}/{total} passed, {failed} failed")

    if all_errors:
        print("\nFailures:")
        for url, errors in all_errors:
            print(f"  {url}:")
            for err in errors:
                print(f"    - {err}")

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_integration_tests())
    sys.exit(0 if success else 1)
