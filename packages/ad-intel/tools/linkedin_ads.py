"""
LinkedIn Ad Library search tool.

Searches the LinkedIn Ad Library for ads by account owner, payer, or keyword.
Returns structured details of ad campaigns including creative content,
impression ranges, and run dates.
"""

import logging

from lib.crawler import extract_structured_data
from lib.url_builder import build_linkedin_ad_library_url

logger = logging.getLogger("ad-intel")

VALID_DATE_OPTIONS = [
    "last-30-days",
    "current-month",
    "current-year",
    "last-year",
    "custom-date-range",
]

EXTRACTION_PROMPT = """\
From the LinkedIn Ad Library page, extract a high-level summary of the ads being run.
Do NOT list every individual ad. Instead extract:
- The total number of results shown (You will see a string like "xx ads match your search criteria", get that xx number)
- The ad formats in use (e.g. single image, video, carousel, text)
- The main themes or topics the ads cover (2-5 bullet points)
- The typical CTA buttons used (e.g. "Learn More", "Sign Up")
"""

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "total_result_count": {
            "type": "string",
            "description": "Result count text shown on page",
        },
        "result_count_numeric": {
            "type": "integer",
            "description": "Parsed numeric count",
        },
        "ad_formats": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Distinct ad formats seen (e.g. single image, video, carousel)",
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
        "date_range": {
            "type": "string",
            "description": "Typical date range ads are running",
        }
    },
}

EMPTY_RESULT = {
    "total_result_count": "0 results",
    "result_count_numeric": 0,
    "ad_formats": [],
    "themes": [],
    "cta_buttons": [],
    "date_range": None,
}

LINKEDIN_ACCESS_WARNING = (
    "LinkedIn Ad Library returned limited results. This may be due to "
    "LinkedIn's access restrictions. For full results, consider accessing "
    "the Ad Library directly at: {url}"
)


async def ad_intel_linkedin_search(
    account_owner: str | None = None,
    payer: str | None = None,
    keyword: str | None = None,
    countries: str | None = None,
    date_option: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    impressions_min_value: int | None = None,
    impressions_max_value: int | None = None,
) -> dict:
    """
    Search the LinkedIn Ad Library for ads.

    At least one of account_owner, payer, or keyword must be provided.

    Args:
        account_owner: Company handle (e.g. "notion", "hubspot").
        payer: Payer name.
        keyword: Keyword search.
        countries: 2-letter code(s), comma-separated (e.g. "US" or "US,GB").
        date_option: One of: last-30-days, current-month, current-year,
                     last-year, custom-date-range.
        start_date: YYYY-MM-DD, required if date_option is custom-date-range.
        end_date: YYYY-MM-DD, required if date_option is custom-date-range.
        impressions_min_value: Min impressions (in thousands).
        impressions_max_value: Max impressions (in thousands).

    Returns:
        Structured dict with total_result_count, result_count_numeric, and ads list.

    Raises:
        ValueError: If no search criteria provided or invalid date options.
    """
    if date_option and date_option not in VALID_DATE_OPTIONS:
        raise ValueError(
            f"Invalid date_option: {date_option}. Must be one of: {VALID_DATE_OPTIONS}"
        )

    # build_linkedin_ad_library_url raises ValueError for missing criteria
    url = build_linkedin_ad_library_url(
        account_owner=account_owner,
        payer=payer,
        keyword=keyword,
        countries=countries,
        date_option=date_option,
        start_date=start_date,
        end_date=end_date,
        impressions_min_value=impressions_min_value,
        impressions_max_value=impressions_max_value,
    )

    search_desc = account_owner or payer or keyword
    logger.info("Searching LinkedIn Ad Library: %s", search_desc)

    try:
        data = await extract_structured_data(
            url=url,
            prompt=EXTRACTION_PROMPT,
            schema=OUTPUT_SCHEMA,
        )

        if not isinstance(data, dict):
            return {
                **EMPTY_RESULT,
                "warning": LINKEDIN_ACCESS_WARNING.format(url=url),
                "search_url": url,
            }

        result = {
            "total_result_count": data.get("total_result_count", "0 results"),
            "result_count_numeric": data.get("result_count_numeric", 0),
            "ad_formats": data.get("ad_formats", []),
            "themes": data.get("themes", []),
            "cta_buttons": data.get("cta_buttons", []),
            "date_range": data.get("date_range"),
            "search_url": url,
        }

        # Add access warning if no results (likely due to LinkedIn restrictions)
        if result["result_count_numeric"] == 0 and not result["themes"]:
            result["warning"] = LINKEDIN_ACCESS_WARNING.format(url=url)

        return result

    except Exception as e:
        logger.error("LinkedIn Ad Library search failed: %s", e)
        return {
            **EMPTY_RESULT,
            "error": str(e),
            "warning": LINKEDIN_ACCESS_WARNING.format(url=url),
            "search_url": url,
        }
