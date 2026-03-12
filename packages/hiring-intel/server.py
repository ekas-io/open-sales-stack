"""
hiring-intel MCP server.

Search job postings across major job boards (LinkedIn, Indeed, Glassdoor, Google,
ZipRecruiter, Bayt) and extract full job descriptions from career page URLs.
"""

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

if _pkg_dir not in sys.path:
    sys.path.insert(0, _pkg_dir)

load_dotenv(os.path.join(_pkg_dir, ".env"))
load_dotenv(os.path.join(_root_dir, ".env"))

# ── Logging ──────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("hiring-intel")

# ── MCP Server ───────────────────────────────────────────────────────────

mcp = FastMCP("open-sales-stack-hiring-intel")

SEARCH_JOBS_DESCRIPTION = """\
Search for job postings across major job boards. Use this to research what roles \
a company is hiring for, understand their growth areas, and identify team structure.

Supported job boards: LinkedIn, Indeed, Glassdoor, Google Jobs, ZipRecruiter, Bayt.

Intended for targeted prospect/account research — not bulk data collection. \
Keep results_wanted low (10-25) and search for specific companies or roles.

Tips:
  - site_name must be a list of strings, e.g. ["linkedin"] or ["indeed", "glassdoor"].
  - For a specific company: use search_term with the company name, or use \
linkedin_company_ids for precise LinkedIn filtering.
  - For Indeed/Glassdoor outside the US: set country_indeed (e.g. "UK", "Germany").
  - For Google Jobs: you must provide google_search_term with Google search syntax.
  - LinkedIn rate-limits aggressively — use Indeed as the primary source when possible.
  - Set linkedin_fetch_description=true to get full descriptions from LinkedIn \
(slower, more requests)."""

EXTRACT_JOB_DESCRIPTION_DESCRIPTION = """\
Extract the full job description from a job posting URL, or crawl a company's \
careers page to discover job listings.

Two modes:
  - 'single' (default): Fetch and extract content from a single job posting URL. \
Returns the page content as markdown.
  - 'crawl': Crawl a company careers page (e.g. https://company.com/careers) to \
discover and extract multiple job listings. Follows links up to max_pages.

Note: LinkedIn job URLs will be blocked — use this for company career sites, \
Greenhouse, Lever, Ashby, Workday, and other ATS platforms."""


@mcp.tool(description=SEARCH_JOBS_DESCRIPTION)
async def search_jobs(
    search_term: Annotated[str, Field(
        description="Job title, company name, or keywords to search for.\n\nExample: `software engineer at Anthropic`; `sales manager`",
    )],
    site_name: Annotated[list[str] | None, Field(
        description="Job boards to search. Must be a list of strings. Valid values: `\"linkedin\"`, `\"indeed\"`, `\"glassdoor\"`, `\"google\"`, `\"zip_recruiter\"`, `\"bayt\"`. Defaults to all sites if omitted.\n\nExample: `[\"linkedin\"]`; `[\"indeed\", \"glassdoor\"]`",
    )] = None,
    location: Annotated[str | None, Field(
        description="City, state, or country to filter jobs by location.\n\nExample: `New York, NY`; `San Francisco, CA`; `London`",
    )] = None,
    distance: Annotated[int | None, Field(
        description="Search radius in miles around the specified location. Only applies when location is set.\n\nExample: `25`; `50`",
    )] = None,
    job_type: Annotated[str | None, Field(
        description="Filter by employment type. Valid values: `\"fulltime\"`, `\"parttime\"`, `\"internship\"`, `\"contract\"`.\n\nExample: `fulltime`",
    )] = None,
    is_remote: Annotated[bool | None, Field(
        description="Set to `true` to return only remote jobs. Set to `false` to exclude remote jobs. Omit to include both.\n\nExample: `true`",
    )] = None,
    results_wanted: Annotated[int, Field(
        description="Number of job postings to return. Keep low (10-25) for targeted research. Maximum is 50.\n\nExample: `10`",
    )] = 10,
    hours_old: Annotated[int | None, Field(
        description="Only return jobs posted within this many hours. Use to find recent postings.\n\nExample: `72` (last 3 days); `168` (last week)",
    )] = None,
    country_indeed: Annotated[str | None, Field(
        description="Country for Indeed and Glassdoor searches outside the US. Use the country name in English.\n\nExample: `UK`; `Germany`; `Canada`",
    )] = None,
    linkedin_fetch_description: Annotated[bool, Field(
        description="Set to `true` to fetch full job descriptions from LinkedIn. Slower and uses more requests, but returns complete job details. Only applies when `site_name` includes `\"linkedin\"`.\n\nExample: `true`",
    )] = False,
    linkedin_company_ids: Annotated[list[int] | None, Field(
        description="LinkedIn company numeric IDs to filter results to specific companies. More precise than using company name in search_term. Find a company's ID from their LinkedIn URL.\n\nExample: `[1441]` (Google); `[1035]` (Microsoft)",
    )] = None,
    google_search_term: Annotated[str | None, Field(
        description="Custom search query for Google Jobs, using Google search syntax. Required when `site_name` includes `\"google\"`.\n\nExample: `software engineer at Stripe site:careers.stripe.com`",
    )] = None,
    easy_apply: Annotated[bool | None, Field(
        description="Set to `true` to return only LinkedIn Easy Apply jobs. Only applies when `site_name` includes `\"linkedin\"`.\n\nExample: `true`",
    )] = None,
    enforce_annual_salary: Annotated[bool, Field(
        description="Set to `true` to normalize all salary figures to annual amounts, filtering out jobs that don't include salary data.\n\nExample: `true`",
    )] = False,
    offset: Annotated[int | None, Field(
        description="Number of results to skip for pagination. Use with `results_wanted` to retrieve subsequent pages.\n\nExample: `10` (skip first 10, get next page)",
    )] = None,
    description_format: Annotated[str, Field(
        description="Output format for job description text. Valid values: `\"markdown\"` (default), `\"html\"`.\n\nExample: `markdown`",
    )] = "markdown",
) -> str:
    """Search for job postings across major job boards."""
    from tools.search_jobs import search_jobs as _search

    return await _search(
        search_term, site_name, location, distance, job_type, is_remote,
        results_wanted, hours_old, country_indeed, linkedin_fetch_description,
        linkedin_company_ids, google_search_term, easy_apply,
        enforce_annual_salary, offset, description_format,
    )


@mcp.tool(description=EXTRACT_JOB_DESCRIPTION_DESCRIPTION)
async def extract_job_description(
    url: Annotated[str, Field(
        description="URL of a single job posting or a company careers page to crawl. LinkedIn job URLs will be blocked — use ATS platforms (Greenhouse, Lever, Ashby, Workday) or company career sites.\n\nExample: `https://boards.greenhouse.io/stripe/jobs/12345`; `https://company.com/careers`",
    )],
    mode: Annotated[str, Field(
        description="Extraction mode. `\"single\"` fetches one job posting URL and returns its full content as markdown. `\"crawl\"` follows links from a careers page to discover multiple job listings up to `max_pages`.\n\nExample: `single`; `crawl`",
    )] = "single",
    max_pages: Annotated[int, Field(
        description="Maximum number of pages to visit when `mode` is `\"crawl\"`. Higher values discover more jobs but take longer.\n\nExample: `5`; `10`",
    )] = 5,
) -> str:
    """Extract job description from a URL or crawl a careers page."""
    from tools.extract_job_description import extract_job_description as _extract

    return await _extract(url, mode, max_pages)


# ── Entry point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run(transport="stdio")
