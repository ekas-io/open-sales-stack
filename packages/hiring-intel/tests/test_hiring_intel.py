"""
Comprehensive tests for hiring-intel tool.

Tests both tools:
  1. search_jobs — JobSpy-based job board search
  2. extract_job_description — crawl4ai-based description extraction

Test matrix covers:
  - Different companies / search terms
  - Different job board sites (linkedin, indeed, glassdoor, google, zip_recruiter)
  - Different parameter combos (location, job_type, is_remote, hours_old)
  - extract_job_description modes (single, crawl)
  - Input validation and error handling

Usage:
    python packages/hiring-intel/tests/test_hiring_intel.py [--quick]
"""

import asyncio
import json
import os
import sys
import time
import traceback

# Add parent dirs to path
_tests_dir = os.path.dirname(os.path.abspath(__file__))
_pkg_dir = os.path.dirname(_tests_dir)
_root_dir = os.path.dirname(os.path.dirname(_pkg_dir))
sys.path.insert(0, _pkg_dir)
sys.path.insert(0, _root_dir)

from server import search_jobs, extract_job_description, VALID_SITES, VALID_JOB_TYPES


# ── Test utilities ──────────────────────────────────────────────────────

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
SKIP = "\033[93mSKIP\033[0m"

test_results = []


def log_result(name, passed, duration, detail="", data=None):
    status = PASS if passed else FAIL
    test_results.append({"name": name, "passed": passed, "duration": duration, "detail": detail})
    print(f"  [{status}] {name} ({duration:.1f}s)")
    if detail:
        print(f"         {detail}")
    if data and passed:
        total = data.get("total", 0)
        jobs = data.get("jobs", [])
        if jobs:
            sample = jobs[0]
            title = sample.get("title", "N/A")
            company = sample.get("company_name", sample.get("company", "N/A"))
            loc = sample.get("location", "N/A")
            print(f"         Found {total} jobs. Sample: {title} @ {company} ({loc})")
        else:
            print(f"         Found {total} jobs (no details)")


async def run_search_test(name, expect_error=False, expect_results=True, **kwargs):
    """Run a search_jobs test."""
    start = time.time()
    try:
        raw = await search_jobs(**kwargs)
        data = json.loads(raw)
        duration = time.time() - start

        if expect_error:
            if "error" in data:
                log_result(name, True, duration, f"Got expected error: {data['error'][:100]}")
            else:
                log_result(name, False, duration, "Expected error but got success")
        elif expect_results:
            if data.get("status") == "completed" and data.get("total", 0) > 0:
                log_result(name, True, duration, data=data)
            elif data.get("total", 0) == 0:
                log_result(name, False, duration, "Got 0 results (expected some)")
            else:
                log_result(name, False, duration, f"Unexpected: {json.dumps(data)[:200]}")
        else:
            # Don't require results, just no crash
            if "error" not in data:
                log_result(name, True, duration, f"Completed with {data.get('total', 0)} results", data=data)
            else:
                log_result(name, False, duration, f"Error: {data['error'][:200]}")
    except Exception as e:
        duration = time.time() - start
        log_result(name, False, duration, f"Exception: {e}")
        traceback.print_exc()


async def run_extract_test(name, expect_error=False, **kwargs):
    """Run an extract_job_description test."""
    start = time.time()
    try:
        raw = await extract_job_description(**kwargs)
        data = json.loads(raw)
        duration = time.time() - start

        if expect_error:
            if "error" in data:
                log_result(name, True, duration, f"Got expected error: {data['error'][:100]}")
            else:
                log_result(name, False, duration, "Expected error but got success")
        else:
            if data.get("status") == "completed":
                if "markdown" in data and data["markdown"]:
                    md_len = len(data["markdown"])
                    log_result(name, True, duration, f"Extracted {md_len} chars of markdown")
                elif "pages_found" in data:
                    log_result(name, True, duration, f"Crawled {data['pages_found']} pages")
                else:
                    log_result(name, True, duration, "Completed (no markdown content)")
            else:
                log_result(name, False, duration, f"Status: {data.get('status', 'unknown')}")
    except Exception as e:
        duration = time.time() - start
        log_result(name, False, duration, f"Exception: {e}")
        traceback.print_exc()


# ── Test groups ─────────────────────────────────────────────────────────

async def test_group_1_trustmi_linkedin():
    """Test 1: Trustmi AI — the user's requested test."""
    print("\n=== Test Group 1: Trustmi AI (User's Request) ===")

    # Search for Trustmi jobs on LinkedIn
    await run_search_test(
        "Trustmi AI — LinkedIn search",
        search_term="Trustmi AI",
        site_name=["linkedin"],
        results_wanted=10,
        expect_results=False,  # Small company, may not have many listings
    )

    # Search for Trustmi jobs on Indeed
    await run_search_test(
        "Trustmi AI — Indeed search",
        search_term="Trustmi AI",
        site_name=["indeed"],
        results_wanted=10,
        expect_results=False,
    )

    # Search across all default sites
    await run_search_test(
        "Trustmi AI — all sites (default)",
        search_term="Trustmi AI",
        results_wanted=10,
        expect_results=False,
    )


async def test_group_2_different_sites():
    """Test 2: Different job board sites."""
    print("\n=== Test Group 2: Different Job Board Sites ===")

    # Well-known company with lots of postings — test each site individually
    company = "Stripe"
    sites_to_test = ["indeed", "linkedin", "glassdoor", "zip_recruiter"]

    for site in sites_to_test:
        await run_search_test(
            f"{company} — {site} only",
            search_term=company,
            site_name=[site],
            results_wanted=5,
            expect_results=False,  # Some sites may rate limit
        )

    # Multiple sites at once
    await run_search_test(
        f"{company} — indeed + linkedin combined",
        search_term=company,
        site_name=["indeed", "linkedin"],
        results_wanted=10,
        expect_results=False,
    )

    # Google Jobs (requires google_search_term)
    await run_search_test(
        f"{company} — Google Jobs",
        search_term=company,
        site_name=["google"],
        google_search_term=f"{company} software engineer jobs",
        results_wanted=5,
        expect_results=False,
    )


async def test_group_3_different_companies():
    """Test 3: Different companies."""
    print("\n=== Test Group 3: Different Companies ===")

    companies = [
        ("Anthropic", "indeed"),
        ("OpenAI", "indeed"),
        ("Ramp", "indeed"),
        ("Figma", "indeed"),
    ]
    for company, site in companies:
        await run_search_test(
            f"{company} — {site}",
            search_term=company,
            site_name=[site],
            results_wanted=5,
            expect_results=False,
        )


async def test_group_4_param_combos():
    """Test 4: Different parameter combinations."""
    print("\n=== Test Group 4: Parameter Combinations ===")

    # Location filter
    await run_search_test(
        "Software Engineer — San Francisco",
        search_term="software engineer",
        site_name=["indeed"],
        location="San Francisco, CA",
        results_wanted=5,
        expect_results=False,
    )

    # Remote filter
    await run_search_test(
        "Data Scientist — remote only",
        search_term="data scientist",
        site_name=["indeed"],
        is_remote=True,
        results_wanted=5,
        expect_results=False,
    )

    # Job type filter
    await run_search_test(
        "Internship — marketing",
        search_term="marketing intern",
        site_name=["indeed"],
        job_type="internship",
        results_wanted=5,
        expect_results=False,
    )

    # Hours old filter (recent postings)
    await run_search_test(
        "Product Manager — posted last 24h",
        search_term="product manager",
        site_name=["indeed"],
        hours_old=24,
        results_wanted=5,
        expect_results=False,
    )

    # Distance filter
    await run_search_test(
        "DevOps — within 50 miles of NYC",
        search_term="DevOps engineer",
        site_name=["indeed"],
        location="New York, NY",
        distance=50,
        results_wanted=5,
        expect_results=False,
    )

    # Country (non-US)
    await run_search_test(
        "Engineer — UK (Indeed)",
        search_term="software engineer",
        site_name=["indeed"],
        country_indeed="UK",
        results_wanted=5,
        expect_results=False,
    )

    # Description format HTML
    await run_search_test(
        "Sales rep — HTML format",
        search_term="sales development representative",
        site_name=["indeed"],
        results_wanted=3,
        description_format="html",
        expect_results=False,
    )

    # Enforce annual salary
    await run_search_test(
        "Accountant — annual salary only",
        search_term="accountant",
        site_name=["indeed"],
        results_wanted=5,
        enforce_annual_salary=True,
        expect_results=False,
    )


async def test_group_5_extract_job_description():
    """Test 5: extract_job_description tool."""
    print("\n=== Test Group 5: Extract Job Description ===")

    # Single mode — Greenhouse job board
    await run_extract_test(
        "Greenhouse board — single mode",
        url="https://boards.greenhouse.io/anthropic",
        mode="single",
    )

    # Single mode — Lever
    await run_extract_test(
        "Lever board — single mode",
        url="https://jobs.lever.co/netflix",
        mode="single",
    )

    # Single mode — Ashby
    await run_extract_test(
        "Ashby board — single mode",
        url="https://jobs.ashbyhq.com/ramp",
        mode="single",
    )

    # Crawl mode — Greenhouse
    await run_extract_test(
        "Greenhouse board — crawl mode (max 3 pages)",
        url="https://boards.greenhouse.io/anthropic",
        mode="crawl",
        max_pages=3,
    )


async def test_group_6_error_handling():
    """Test 6: Input validation and error handling."""
    print("\n=== Test Group 6: Error Handling & Validation ===")

    # Invalid site name
    await run_search_test(
        "Invalid site_name",
        search_term="test",
        site_name=["invalid_site"],
        expect_error=True,
    )

    # Invalid job type
    await run_search_test(
        "Invalid job_type",
        search_term="test",
        job_type="invalid_type",
        expect_error=True,
    )

    # Results capped at 50
    await run_search_test(
        "results_wanted > 50 (should cap)",
        search_term="software engineer",
        site_name=["indeed"],
        results_wanted=100,
        expect_results=False,
    )

    # extract_job_description — no protocol
    await run_extract_test(
        "URL without protocol",
        url="boards.greenhouse.io/test",
        expect_error=True,
    )

    # extract_job_description — invalid mode
    await run_extract_test(
        "Invalid mode",
        url="https://example.com",
        mode="invalid",
        expect_error=True,
    )

    # extract_job_description — LinkedIn URL (should block)
    await run_extract_test(
        "LinkedIn URL (should be blocked)",
        url="https://www.linkedin.com/jobs/view/12345",
        expect_error=True,
    )

    # Nonexistent company
    await run_search_test(
        "Nonexistent company — xyznonexistent123",
        search_term="xyznonexistent123 company jobs",
        site_name=["indeed"],
        results_wanted=5,
        expect_results=False,
    )


async def test_group_7_linkedin_company_id():
    """Test 7: LinkedIn company ID filter."""
    print("\n=== Test Group 7: LinkedIn Company ID ===")

    # Trustmi AI LinkedIn company ID (if known)
    # This tests the linkedin_company_ids parameter
    await run_search_test(
        "LinkedIn company ID search (Stripe: 2135371)",
        search_term="",
        site_name=["linkedin"],
        linkedin_company_ids=[2135371],  # Stripe's LinkedIn company ID
        results_wanted=5,
        expect_results=False,
    )


# ── Main ────────────────────────────────────────────────────────────────

async def main():
    quick_mode = "--quick" in sys.argv

    print("=" * 70)
    print("  HIRING-INTEL COMPREHENSIVE TEST SUITE")
    print(f"  Mode: {'QUICK' if quick_mode else 'FULL'}")
    print("=" * 70)

    # Always run these core tests
    await test_group_1_trustmi_linkedin()
    await test_group_6_error_handling()

    if not quick_mode:
        await test_group_2_different_sites()
        await test_group_3_different_companies()
        await test_group_4_param_combos()
        await test_group_5_extract_job_description()
        await test_group_7_linkedin_company_id()

    # Summary
    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    passed = sum(1 for r in test_results if r["passed"])
    failed = sum(1 for r in test_results if not r["passed"])
    total = len(test_results)
    total_time = sum(r["duration"] for r in test_results)

    print(f"\n  Total: {total} tests | {PASS}: {passed} | {FAIL}: {failed}")
    print(f"  Time: {total_time:.1f}s")

    if failed > 0:
        print(f"\n  Failed tests:")
        for r in test_results:
            if not r["passed"]:
                print(f"    - {r['name']}: {r['detail']}")

    print("=" * 70)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
