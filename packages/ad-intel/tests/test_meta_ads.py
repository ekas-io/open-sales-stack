"""
End-to-end tests for Meta Ad Library tool.

Requires: OPENAI_API_KEY set for LLM extraction.
Run with: pytest packages/ad-intel/tests/test_meta_ads.py -v -s
"""

import os
import sys

import pytest

# Add package dir to path for imports
_pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _pkg_dir not in sys.path:
    sys.path.insert(0, _pkg_dir)

from tools.meta_ads import ad_intel_meta_search  # noqa: E402


# Test 1: Basic keyword search — well-known advertiser
@pytest.mark.asyncio
async def test_meta_search_anthropic():
    """Search for 'Anthropic' ads in US. Anthropic runs Meta ads regularly."""
    result = await ad_intel_meta_search(query="Anthropic", country="US")

    assert result["result_count_numeric"] > 0, "Anthropic should have active Meta ads"
    assert len(result["ads"]) > 0, "Should return at least one ad"

    # Verify ad structure
    first_ad = result["ads"][0]
    assert first_ad.get("advertiser_name"), "Ad should have advertiser name"
    assert first_ad.get("started_running_on"), "Ad should have start date"

    print(f"Found {result['result_count_numeric']} Anthropic ads")
    print(f"First ad CTA: {first_ad.get('cta_button', 'N/A')}")


# Test 2: Search with date range
@pytest.mark.asyncio
async def test_meta_search_with_date_range():
    """Search for 'HubSpot' ads with a date range filter."""
    result = await ad_intel_meta_search(
        query="HubSpot",
        country="US",
        start_date_min="2025-01-01",
        start_date_max="2025-12-31",
    )

    assert result["result_count_numeric"] >= 0, "Should return a valid count"

    if len(result["ads"]) > 0:
        for ad in result["ads"][:3]:
            print(
                f"  [{ad.get('started_running_on')}] "
                f"{ad.get('headline', 'No headline')} — "
                f"CTA: {ad.get('cta_button', 'N/A')}"
            )


# Test 3: Non-US country
@pytest.mark.asyncio
async def test_meta_search_india():
    """Search for 'Freshworks' ads in India."""
    result = await ad_intel_meta_search(query="Freshworks", country="IN")

    assert isinstance(result["ads"], list), "Ads should be a list"
    print(f"Found {result['result_count_numeric']} Freshworks ads in India")


# Test 4: Niche / low-volume search
@pytest.mark.asyncio
async def test_meta_search_low_volume():
    """Search for a niche term that might have few or zero results."""
    result = await ad_intel_meta_search(query="xyznonexistentbrand12345")

    assert (
        result["result_count_numeric"] == 0
        or result["result_count_numeric"] is not None
    )
    print(f"Low-volume search returned: {result['total_result_count']}")


# Test 5: Ad type filter
@pytest.mark.asyncio
async def test_meta_search_political_ads():
    """Search for political/issue ads."""
    result = await ad_intel_meta_search(
        query="climate",
        country="US",
        ad_type="political_and_issue_ads",
    )

    assert isinstance(result["ads"], list)
    print(f"Found {result['result_count_numeric']} political ads about 'climate'")


# Test 6: Validate ad structure completeness
@pytest.mark.asyncio
async def test_meta_ad_structure():
    """Verify all expected fields are present in returned ads."""
    result = await ad_intel_meta_search(query="Salesforce", country="US")

    assert len(result["ads"]) > 0, "Salesforce should have active ads"

    ad = result["ads"][0]
    expected_fields = [
        "advertiser_name",
        "primary_text",
        "cta_button",
        "started_running_on",
        "media_type",
    ]
    for field in expected_fields:
        assert field in ad, f"Ad missing expected field: {field}"
