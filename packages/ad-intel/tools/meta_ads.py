"""
Meta Ad Library search tool.

Searches the Meta Ad Library for active ads by keyword, advertiser, or topic.
Returns structured details including ad count, creative details, CTAs, and run dates.
"""

import logging

from lib.crawler import extract_structured_data
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
Extract all visible ad results from the Meta Ad Library page.
For each ad, extract:
- The advertiser/page name
- The ad creative text / primary text / body copy
- The headline (if present)
- The call-to-action button text (e.g. "Learn More", "Sign Up", "Shop Now")
- The description or link description
- The "Started running on" date
- The platform(s) the ad runs on (Facebook, Instagram, Messenger, Audience Network)
- Whether the ad contains an image, video, or carousel
- Any visible landing page URL or domain

Also extract the total result count shown at the top of the page \
(e.g. "~220 results" or "About 220 results"). This is typically displayed \
near the top as "X results" with a subtitle like \
"These results include ads that match your keyword search."
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
        "ads": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "advertiser_name": {"type": "string"},
                    "primary_text": {
                        "type": "string",
                        "description": "The main ad body/creative text",
                    },
                    "headline": {"type": "string"},
                    "description": {
                        "type": "string",
                        "description": "Link description or secondary text",
                    },
                    "cta_button": {
                        "type": "string",
                        "description": "Call to action text, e.g. Learn More, Sign Up",
                    },
                    "started_running_on": {
                        "type": "string",
                        "description": "Date the ad started running, e.g. Mar 1, 2026",
                    },
                    "platforms": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Platforms: Facebook, Instagram, Messenger, Audience Network",
                    },
                    "media_type": {
                        "type": "string",
                        "description": "image, video, or carousel",
                    },
                    "landing_page_url": {"type": "string"},
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
        data = await extract_structured_data(
            url=url,
            prompt=EXTRACTION_PROMPT,
            schema=OUTPUT_SCHEMA,
            mode="scrape",
            delay_before_return_html=5,
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
