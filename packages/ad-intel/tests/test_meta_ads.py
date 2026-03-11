"""
End-to-end tests for Meta Ad Library tool.

Requires: LLM_API_KEY set for LLM extraction.
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


# Test 1: End-to-end search — verifies full LLM extraction pipeline and ad structure
@pytest.mark.asyncio
async def test_meta_search_anthropic():
    """Search for 'Anthropic' ads in US and verify structure of returned ads."""
    result = await ad_intel_meta_search(query="Anthropic", country="US")

    assert result["result_count_numeric"] > 0, "Anthropic should have active Meta ads"
    assert len(result["ads"]) > 0, "Should return at least one ad"

    ad = result["ads"][0]
    assert "advertiser_name" in ad, "Ad missing advertiser_name"

    print(f"Found {result['result_count_numeric']} Anthropic ads")
    print(f"Formats: {result.get('ad_formats')} | Themes: {result.get('themes')}")


# Test 2: Zero-results edge case — fast (no LLM call, pre-check detects 0 results)
@pytest.mark.asyncio
async def test_meta_search_low_volume():
    """Search for a nonexistent brand — verifies zero-results short-circuit (no LLM)."""
    result = await ad_intel_meta_search(query="xyznonexistentbrand12345")

    assert result["result_count_numeric"] == 0
    assert result["ads"] == []
    print(f"Low-volume search returned: {result['total_result_count']}")
