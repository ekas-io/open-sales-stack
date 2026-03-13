"""
End-to-end tests for LinkedIn Ad Library tool.

Requires: LLM_API_KEY set for LLM extraction.

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


# Test 1: End-to-end account owner search — verifies the full LLM extraction pipeline
@pytest.mark.asyncio
async def test_linkedin_search_mesh_security():
    """Search for Mesh Security's LinkedIn ads (last 30 days) and verify the full extraction pipeline."""
    result = await ad_intel_linkedin_search(
        account_owner="Mesh Security", date_option="last-30-days"
    )

    assert "result_count_numeric" in result, "Should return result count"
    assert "themes" in result, "Should return themes"
    assert "ad_formats" in result, "Should return ad_formats"
    assert "cta_buttons" in result, "Should return cta_buttons"
    assert result.get("result_count_numeric", 0) > 0, (
        f"Expected >0 ads but got {result.get('result_count_numeric')}"
    )

    print(f"Found {result['result_count_numeric']} Mesh Security ads")
    print(f"  Themes: {result.get('themes')}")
    print(f"  Formats: {result.get('ad_formats')}")
    print(f"  CTAs: {result.get('cta_buttons')}")


# Test 2: Validation — no search criteria should error (fast, no LLM call)
@pytest.mark.asyncio
async def test_linkedin_search_validation_error():
    """Should raise an error when no search criteria provided."""
    with pytest.raises(ValueError, match="(?i)at least one of"):
        await ad_intel_linkedin_search(countries="US")


# Test 3: Validation — custom date range without dates should error (fast, no LLM call)
@pytest.mark.asyncio
async def test_linkedin_custom_date_validation():
    """Should raise error when custom-date-range used without start/end dates."""
    with pytest.raises(ValueError, match="start_date.*end_date"):
        await ad_intel_linkedin_search(
            account_owner="notion",
            date_option="custom-date-range",
        )
