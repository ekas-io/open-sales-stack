"""
ad-intel MCP server.

Provides competitive ad intelligence from Meta Ad Library and LinkedIn Ad Library.
Uses crawl4ai-based extraction to return structured ad data.

Run directly: python packages/ad-intel/server.py
"""

import json
import logging
import os
import sys
from typing import Annotated

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from pydantic import Field

# ── Environment ──────────────────────────────────────────────────────────

_pkg_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.dirname(os.path.dirname(_pkg_dir))

# Add package dir to path so tools/ and lib/ are importable
if _pkg_dir not in sys.path:
    sys.path.insert(0, _pkg_dir)

load_dotenv(os.path.join(_pkg_dir, ".env"))
load_dotenv(os.path.join(_root_dir, ".env"))

# ── Logging ──────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stderr,  # Keep stdout clean for MCP JSON-RPC
)
logger = logging.getLogger("ad-intel")

# ── MCP Server ──────────────────────────────────────────────────────────

mcp = FastMCP("open-sales-stack-ad-intel")

# ── Tool descriptions ───────────────────────────────────────────────────

META_TOOL_DESCRIPTION = """\
Search the Meta Ad Library for active ads by keyword, advertiser, or topic. \
Returns structured details of ads including ad count, individual ad creative \
details, CTAs, and run dates.

Use this to research competitor ad strategies on Facebook and Instagram, \
discover ad creative patterns, and track advertising activity.

Examples:
  - Search for a company's ads: query="Anthropic", country="US"
  - Filter by ad type: query="climate", ad_type="political_and_issue_ads"
  - Date range: query="HubSpot", start_date_min="2025-01-01", start_date_max="2025-12-31"

Returns: total result count, and for each ad: advertiser name, primary text, \
headline, CTA button, start date, platforms, media type, and landing page URL."""

LINKEDIN_TOOL_DESCRIPTION = """\
Search the LinkedIn Ad Library for ads by account owner, payer, or keyword. \
Returns structured details of ad campaigns including creative content, \
impression ranges, and run dates.

Use this to research competitor LinkedIn ad strategies, discover B2B ad \
creative patterns, and track advertising spend by impression ranges.

At least one of account_owner, payer, or keyword must be provided.

Examples:
  - Company ads: account_owner="notion", countries="US"
  - Keyword search: keyword="sales automation", countries="US"
  - Date filtered: account_owner="hubspot", date_option="last-30-days"
  - Impression range: account_owner="notion", impressions_min_value=1, \
impressions_max_value=10

Note: LinkedIn Ad Library may return limited results due to access restrictions. \
The tool will include a warning and direct URL when this occurs.

Returns: total result count, and for each ad: advertiser name, ad format, \
primary text, headline, CTA, impression range, date range, active status, \
landing page URL, and payer info."""


# ── Meta Ad Library tool ────────────────────────────────────────────────


@mcp.tool(description=META_TOOL_DESCRIPTION)
async def ad_intel_meta_search(
    query: Annotated[str, Field(
        description="Keyword, advertiser name, or topic to search for in the Meta Ad Library.\n\nExample: `Anthropic`; `HubSpot`; `climate change`",
    )],
    country: Annotated[str, Field(
        description="Two-letter ISO country code to filter ads by the country they ran in.\n\nExample: `US`; `GB`; `DE`",
    )] = "US",
    ad_type: Annotated[str, Field(
        description="Category of ads to return. Valid values: `\"all\"`, `\"political_and_issue_ads\"`, `\"housing_ads\"`, `\"employment_ads\"`, `\"credit_ads\"`.\n\nExample: `all`; `political_and_issue_ads`",
    )] = "all",
    start_date_min: Annotated[str | None, Field(
        description="Filter to ads that started on or after this date. Format: `YYYY-MM-DD`.\n\nExample: `2025-01-01`",
    )] = None,
    start_date_max: Annotated[str | None, Field(
        description="Filter to ads that started on or before this date. Format: `YYYY-MM-DD`.\n\nExample: `2025-12-31`",
    )] = None,
) -> str:
    """Search the Meta Ad Library for active ads."""
    from tools.meta_ads import ad_intel_meta_search as _search

    try:
        result = await _search(
            query=query,
            country=country,
            ad_type=ad_type,
            start_date_min=start_date_min,
            start_date_max=start_date_max,
        )

        # Build summary line
        count = result.get("result_count_numeric", 0)
        summary = f"Found {count} active Meta ads for '{query}' in {country}"

        if count == 0 and not result.get("ads"):
            return json.dumps({
                "summary": f"No active Meta ads found for '{query}' in {country}",
                **result,
            }, default=str)

        return json.dumps({
            "summary": summary,
            **result,
        }, default=str)

    except ValueError as e:
        return json.dumps({"error": str(e), "status": "validation_error"})
    except Exception as e:
        logger.error("Meta Ad Library search failed: %s", e)
        return json.dumps({"error": str(e), "status": "failed"})


# ── LinkedIn Ad Library tool ────────────────────────────────────────────


@mcp.tool(description=LINKEDIN_TOOL_DESCRIPTION)
async def ad_intel_linkedin_search(
    account_owner: Annotated[str | None, Field(
        description="Name of the company or advertiser that owns the LinkedIn ad account. At least one of account_owner, payer, or keyword must be provided.\n\nExample: `notion`; `hubspot`; `anthropic`",
    )] = None,
    payer: Annotated[str | None, Field(
        description="Name of the entity that paid for the ads. Often the same as account_owner, but can differ for agencies.\n\nExample: `notion`; `hubspot`",
    )] = None,
    keyword: Annotated[str | None, Field(
        description="Keyword to search for in ad content. At least one of account_owner, payer, or keyword must be provided.\n\nExample: `sales automation`; `AI assistant`",
    )] = None,
    countries: Annotated[str | None, Field(
        description="Comma-separated list of two-letter ISO country codes to filter ads by geography.\n\nExample: `US`; `US,GB,DE`",
    )] = None,
    date_option: Annotated[str | None, Field(
        description="Preset date range filter. Valid values: `\"last-30-days\"`, `\"current-month\"`, `\"current-year\"`, `\"last-year\"`, `\"custom-date-range\"`. Use `\"custom-date-range\"` with start_date and end_date for a specific range.\n\nExample: `last-30-days`; `current-year`",
    )] = None,
    start_date: Annotated[str | None, Field(
        description="Start of a custom date range. Only used when date_option is `\"custom-date-range\"`. Format: `YYYY-MM-DD`.\n\nExample: `2025-01-01`",
    )] = None,
    end_date: Annotated[str | None, Field(
        description="End of a custom date range. Only used when date_option is `\"custom-date-range\"`. Format: `YYYY-MM-DD`.\n\nExample: `2025-06-30`",
    )] = None,
    impressions_min_value: Annotated[int | None, Field(
        description="Minimum impression tier (1-10). LinkedIn reports impressions in ranges rather than exact counts. Use with impressions_max_value to filter by spend level.\n\nExample: `1`",
    )] = None,
    impressions_max_value: Annotated[int | None, Field(
        description="Maximum impression tier (1-10). LinkedIn reports impressions in ranges rather than exact counts. Use with impressions_min_value to filter by spend level.\n\nExample: `10`",
    )] = None,
) -> str:
    """Search the LinkedIn Ad Library for ads."""
    from tools.linkedin_ads import ad_intel_linkedin_search as _search

    try:
        result = await _search(
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

        # Build summary line
        search_term = account_owner or payer or keyword or "unknown"
        count = result.get("result_count_numeric", 0)
        summary = f"Found {count} LinkedIn ads for '{search_term}'"

        if count == 0 and not result.get("ads"):
            return json.dumps({
                "summary": f"No LinkedIn ads found for '{search_term}'",
                **result,
            }, default=str)

        return json.dumps({
            "summary": summary,
            **result,
        }, default=str)

    except ValueError as e:
        return json.dumps({"error": str(e), "status": "validation_error"})
    except Exception as e:
        logger.error("LinkedIn Ad Library search failed: %s", e)
        return json.dumps({"error": str(e), "status": "failed"})


# ── Entry point ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run(transport="stdio")
