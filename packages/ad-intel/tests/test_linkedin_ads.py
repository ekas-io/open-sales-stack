"""
End-to-end tests for LinkedIn Ad Library tool.

Requires: running crawl4ai instance at CRAWL4AI_BASE_URL (default localhost:11235)

NOTE: LinkedIn Ad Library may require authentication for full results.
Some tests may return 0 results due to LinkedIn's access restrictions.
The tool should handle this gracefully.

Run with: pytest packages/ad-intel/tests/test_linkedin_ads.py -v -s
"""

import os
import sys

import pytest

# Add package dir to path for imports
_pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _pkg_dir not in sys.path:
    sys.path.insert(0, _pkg_dir)

from tools.linkedin_ads import ad_intel_linkedin_search  # noqa: E402


# Test 1: Account owner search
@pytest.mark.asyncio
async def test_linkedin_search_notion():
    """Search for Notion's LinkedIn ads."""
    result = await ad_intel_linkedin_search(account_owner="notion", countries="US")

    assert "ads" in result, "Should return ads array"
    assert "result_count_numeric" in result, "Should return result count"

    print(f"Found {result['result_count_numeric']} Notion ads")
    if result["ads"]:
        ad = result["ads"][0]
        print(f"  Format: {ad.get('ad_format')} | CTA: {ad.get('cta_button')}")


# Test 2: Custom date range
@pytest.mark.asyncio
async def test_linkedin_search_date_range():
    """Search with custom date range for HubSpot ads."""
    result = await ad_intel_linkedin_search(
        account_owner="hubspot",
        countries="US",
        date_option="custom-date-range",
        start_date="2026-01-01",
        end_date="2026-03-08",
    )

    assert isinstance(result["ads"], list)
    print(f"Found {result['result_count_numeric']} HubSpot ads in date range")


# Test 3: Keyword search
@pytest.mark.asyncio
async def test_linkedin_search_keyword():
    """Search by keyword across all advertisers."""
    result = await ad_intel_linkedin_search(
        keyword="sales automation", countries="US"
    )

    assert isinstance(result["ads"], list)
    print(f"Found {result['result_count_numeric']} ads for 'sales automation'")


# Test 4: Impression range filter
@pytest.mark.asyncio
async def test_linkedin_search_impressions():
    """Search with impression range filter."""
    result = await ad_intel_linkedin_search(
        account_owner="notion",
        countries="US",
        date_option="last-30-days",
        impressions_min_value=1,
        impressions_max_value=10,
    )

    assert isinstance(result["ads"], list)
    print(
        f"Found {result['result_count_numeric']} Notion ads "
        f"with 1K-10K impressions in last 30 days"
    )


# Test 5: Validation — no search criteria should error
@pytest.mark.asyncio
async def test_linkedin_search_validation_error():
    """Should raise an error when no search criteria provided."""
    with pytest.raises(ValueError, match="(?i)at least one of"):
        await ad_intel_linkedin_search(countries="US")


# Test 6: Validation — custom date range without dates should error
@pytest.mark.asyncio
async def test_linkedin_custom_date_validation():
    """Should raise error when custom-date-range used without start/end dates."""
    with pytest.raises(ValueError, match="start_date.*end_date"):
        await ad_intel_linkedin_search(
            account_owner="notion",
            date_option="custom-date-range",
        )


# Test 7: Multi-country search
@pytest.mark.asyncio
async def test_linkedin_search_multi_country():
    """Search across multiple countries."""
    result = await ad_intel_linkedin_search(
        account_owner="salesforce", countries="US,GB"
    )

    assert isinstance(result["ads"], list)
    print(f"Found {result['result_count_numeric']} Salesforce ads in US+GB")


# Test 8: Payer-based search
@pytest.mark.asyncio
async def test_linkedin_search_payer():
    """Search by payer."""
    result = await ad_intel_linkedin_search(payer="notion")

    assert isinstance(result["ads"], list)
    print(f"Found {result['result_count_numeric']} ads paid by Notion")


# Test 9: Preset date option
@pytest.mark.asyncio
async def test_linkedin_search_current_year():
    """Search with current-year date option."""
    result = await ad_intel_linkedin_search(
        account_owner="anthropic", date_option="current-year"
    )

    assert isinstance(result["ads"], list)
    print(f"Found {result['result_count_numeric']} Anthropic ads this year")
