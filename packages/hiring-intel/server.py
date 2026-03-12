"""
hiring-intel MCP server.

Search job postings across major job boards (LinkedIn, Indeed, Glassdoor, Google,
ZipRecruiter, Bayt) and extract full job descriptions from career page URLs.
"""

import logging
import os
import sys

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

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
    search_term: str,
    site_name: list[str] | None = None,
    location: str | None = None,
    distance: int | None = None,
    job_type: str | None = None,
    is_remote: bool | None = None,
    results_wanted: int = 10,
    hours_old: int | None = None,
    country_indeed: str | None = None,
    linkedin_fetch_description: bool = False,
    linkedin_company_ids: list[int] | None = None,
    google_search_term: str | None = None,
    easy_apply: bool | None = None,
    enforce_annual_salary: bool = False,
    offset: int | None = None,
    description_format: str = "markdown",
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
    url: str,
    mode: str = "single",
    max_pages: int = 5,
) -> str:
    """Extract job description from a URL or crawl a careers page."""
    from tools.extract_job_description import extract_job_description as _extract

    return await _extract(url, mode, max_pages)


# ── Entry point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run(transport="stdio")
