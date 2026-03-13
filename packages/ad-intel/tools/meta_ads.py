"""
Meta Ad Library search tool.

Searches the Meta Ad Library for active ads by keyword, advertiser, or topic.
Returns structured details including ad count, creative details, CTAs, and run dates.
"""

import logging
import re

from lib.crawler import extract_structured_data, fetch_markdown
from lib.url_builder import build_meta_ad_library_url

logger = logging.getLogger("ad-intel")

VALID_AD_TYPES = [
    "all",
    "political_and_issue_ads",
    "housing_ads",
    "employment_ads",
    "credit_ads",
]

EXTRACTION_PROMPT = """\
From the Meta Ad Library page, extract a high-level summary of the ads being run.
Do NOT list every individual ad. Instead extract:
- The total result count shown at the top (e.g. "~220 results" or "About 220 results")
- The ad formats in use (image, video, carousel, etc.)
- The main themes or topics the ads cover (2-5 bullet points)
- The typical CTA buttons used (e.g. "Learn More", "Sign Up", "Shop Now")
- The platforms the ads run on (Facebook, Instagram, etc.)
- A sample of up to 5 individual ads with basic details
"""

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "total_result_count": {
            "type": "string",
            "description": "The result count string shown at the top, e.g. '~220 results'",
        },
        "result_count_numeric": {
            "type": "integer",
            "description": "Parsed numeric count of total results, e.g. 220",
        },
        "ad_formats": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Distinct ad formats seen (e.g. image, video, carousel)",
        },
        "themes": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Main topics or themes the ads cover",
        },
        "cta_buttons": {
            "type": "array",
            "items": {"type": "string"},
            "description": "CTA button labels observed",
        },
        "platforms": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Platforms ads run on",
        },
        "ads": {
            "type": "array",
            "description": "Sample of individual ads (up to 5)",
            "items": {
                "type": "object",
                "properties": {
                    "advertiser_name": {"type": "string"},
                    "primary_text": {"type": "string"},
                    "headline": {"type": "string"},
                    "cta_button": {"type": "string"},
                    "started_running_on": {"type": "string"},
                    "media_type": {"type": "string"},
                },
            },
        },
    },
}

EMPTY_RESULT = {
    "total_result_count": "0 results",
    "result_count_numeric": 0,
    "ads": [],
}


async def ad_intel_meta_search(
    query: str,
    country: str = "US",
    ad_type: str = "all",
    start_date_min: str | None = None,
    start_date_max: str | None = None,
) -> dict:
    """
    Search the Meta Ad Library for active ads.

    Args:
        query: Search keyword or advertiser name (e.g. "Anthropic", "HubSpot").
        country: 2-letter country code (default: "US").
        ad_type: One of: all, political_and_issue_ads, housing_ads,
                 employment_ads, credit_ads.
        start_date_min: Optional start date filter (YYYY-MM-DD).
        start_date_max: Optional end date filter (YYYY-MM-DD).

    Returns:
        Structured dict with total_result_count, result_count_numeric, and ads list.
    """
    if ad_type not in VALID_AD_TYPES:
        raise ValueError(
            f"Invalid ad_type: {ad_type}. Must be one of: {VALID_AD_TYPES}"
        )

    url = build_meta_ad_library_url(
        query=query,
        country=country,
        ad_type=ad_type,
        start_date_min=start_date_min,
        start_date_max=start_date_max,
    )

    logger.info("Searching Meta Ad Library: query=%s country=%s", query, country)

    try:
        # Quick pre-check: fetch raw markdown to detect zero results without LLM.
        # Look for a non-zero result count (e.g. "~230 results", "About 45 results").
        # If no such pattern is found, the page has no ads — skip the LLM call.
        raw_md = await fetch_markdown(url, delay_before_return_html=3)
        has_results = bool(re.search(r"[1-9]\d*\s*results?", raw_md, re.IGNORECASE))
        if raw_md and not has_results:
            logger.info("Zero results detected for query=%s, skipping LLM extraction", query)
            return {**EMPTY_RESULT, "search_url": url}

        data = await extract_structured_data(
            url=url,
            prompt=EXTRACTION_PROMPT,
            schema=OUTPUT_SCHEMA,
        )

        # Normalize the response shape
        if not isinstance(data, dict):
            return {**EMPTY_RESULT, "search_url": url}

        return {
            "total_result_count": data.get("total_result_count", "0 results"),
            "result_count_numeric": data.get("result_count_numeric", 0),
            "ads": data.get("ads", []),
            "search_url": url,
        }

    except Exception as e:
        logger.error("Meta Ad Library search failed: %s", e)
        return {
            **EMPTY_RESULT,
            "error": str(e),
            "search_url": url,
        }
