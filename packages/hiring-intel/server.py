"""
hiring-intel MCP server.

Search job postings across major job boards (LinkedIn, Indeed, Glassdoor, Google,
ZipRecruiter, Bayt) and extract full job descriptions from career page URLs.

Uses python-jobspy for job board searches and crawl4ai for job description extraction.
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# ── Environment ──────────────────────────────────────────────────────────

_pkg_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.dirname(os.path.dirname(_pkg_dir))

load_dotenv(os.path.join(_pkg_dir, ".env"))
load_dotenv(os.path.join(_root_dir, ".env"))

# Optional proxy/SSL config via env vars
JOBSPY_PROXIES = os.environ.get("JOBSPY_PROXIES", "")
JOBSPY_CA_CERT = os.environ.get("JOBSPY_CA_CERT", "")

# ── Logging ──────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("hiring-intel")

# ── Shared crawl4ai instance ────────────────────────────────────────────

_crawler = None


async def get_crawler():
    """Lazily initialize a shared browser instance for job description extraction."""
    global _crawler
    if _crawler is None:
        from crawl4ai import AsyncWebCrawler, BrowserConfig

        browser_config = BrowserConfig(headless=True)
        _crawler = AsyncWebCrawler(config=browser_config)
        await _crawler.__aenter__()
    return _crawler


# ── JobSpy search logic ─────────────────────────────────────────────────

VALID_SITES = ["linkedin", "indeed", "glassdoor", "google", "zip_recruiter", "bayt"]
VALID_JOB_TYPES = ["fulltime", "parttime", "internship", "contract"]


def _parse_proxy_list() -> list[str] | None:
    """Parse JOBSPY_PROXIES env var into a list."""
    if not JOBSPY_PROXIES:
        return None
    proxies = [p.strip() for p in JOBSPY_PROXIES.split(",") if p.strip()]
    return proxies if proxies else None


def _run_jobspy_search(
    search_term: str,
    location: str | None,
    site_name: list[str] | None,
    distance: int | None,
    job_type: str | None,
    is_remote: bool | None,
    results_wanted: int,
    hours_old: int | None,
    country_indeed: str | None,
    linkedin_fetch_description: bool,
    linkedin_company_ids: list[int] | None,
    google_search_term: str | None,
    easy_apply: bool | None,
    enforce_annual_salary: bool,
    offset: int | None,
    description_format: str,
) -> list[dict]:
    """Run JobSpy scrape_jobs and return results as list of dicts."""
    from jobspy import scrape_jobs

    kwargs = {
        "search_term": search_term,
        "results_wanted": results_wanted,
        "description_format": description_format,
        "enforce_annual_salary": enforce_annual_salary,
        "verbose": 0,
    }

    if site_name:
        kwargs["site_name"] = site_name
    else:
        kwargs["site_name"] = ["indeed", "linkedin", "glassdoor", "google", "zip_recruiter"]
    if location:
        kwargs["location"] = location
    if distance is not None:
        kwargs["distance"] = distance
    if job_type:
        kwargs["job_type"] = job_type
    if is_remote is not None:
        kwargs["is_remote"] = is_remote
    if hours_old is not None:
        kwargs["hours_old"] = hours_old
    if country_indeed:
        kwargs["country_indeed"] = country_indeed
    if linkedin_fetch_description:
        kwargs["linkedin_fetch_description"] = True
    if linkedin_company_ids:
        kwargs["linkedin_company_ids"] = linkedin_company_ids
    if google_search_term:
        kwargs["google_search_term"] = google_search_term
    if easy_apply is not None:
        kwargs["easy_apply"] = easy_apply
    if offset is not None:
        kwargs["offset"] = offset

    # Proxy & SSL from env vars
    proxies = _parse_proxy_list()
    if proxies:
        kwargs["proxies"] = proxies
    if JOBSPY_CA_CERT:
        kwargs["ca_cert"] = JOBSPY_CA_CERT

    df = scrape_jobs(**kwargs)

    if df.empty:
        return []

    # Convert DataFrame to list of dicts, dropping NaN values
    records = df.where(df.notnull(), None).to_dict(orient="records")

    # Clean up records — convert non-serializable types
    cleaned = []
    for record in records:
        clean = {}
        for k, v in record.items():
            if v is None:
                continue
            if hasattr(v, "isoformat"):
                clean[k] = v.isoformat()
            elif isinstance(v, (int, float, str, bool)):
                clean[k] = v
            else:
                clean[k] = str(v)
        cleaned.append(clean)

    return cleaned


# ── crawl4ai job description extraction ─────────────────────────────────


async def _extract_job_description(url: str) -> dict:
    """Extract job description from a URL using crawl4ai."""
    from crawl4ai import CrawlerRunConfig

    crawler = await get_crawler()
    config = CrawlerRunConfig(
        wait_until="networkidle",
        page_timeout=20000,
    )
    result = await crawler.arun(url=url, config=config)

    if not result.success:
        error_msg = getattr(result, "error_message", "unknown error")
        raise RuntimeError(f"Failed to fetch page: {error_msg}")

    return {
        "url": url,
        "markdown": result.markdown if result.markdown else None,
        "status": "completed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def _crawl_careers_page(url: str, max_pages: int) -> dict:
    """Crawl a company careers page to discover and extract job listings."""
    from crawl4ai import CrawlerRunConfig
    from crawl4ai.deep_crawling import BFSDeepCrawlStrategy

    crawler = await get_crawler()
    config = CrawlerRunConfig(
        wait_until="networkidle",
        page_timeout=20000,
        deep_crawl_strategy=BFSDeepCrawlStrategy(
            max_depth=2,
            max_pages=max_pages,
            include_external=False,
        ),
    )
    result = await crawler.arun(url=url, config=config)

    results = result if isinstance(result, list) else [result]

    pages = []
    for r in results:
        if not r.success:
            continue
        pages.append({
            "url": r.url,
            "markdown": r.markdown if r.markdown else None,
        })

    return {
        "careers_url": url,
        "pages_found": len(pages),
        "pages": pages,
        "status": "completed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── MCP Server ──────────────────────────────────────────────────────────

mcp = FastMCP("open-sales-stack-hiring-intel")

SEARCH_JOBS_DESCRIPTION = """\
Search for job postings across major job boards. Use this to research what roles \
a company is hiring for, understand their growth areas, and identify team structure.

Supported job boards: LinkedIn, Indeed, Glassdoor, Google Jobs, ZipRecruiter, Bayt.

Intended for targeted prospect/account research — not bulk data collection. \
Keep results_wanted low (10-25) and search for specific companies or roles.

Tips:
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
Greenhouse, Lever, Ashby, Workday, and other ATS platforms.

Use 'single' mode when you already have a job URL from search_jobs results. \
Use 'crawl' mode to discover jobs directly from a company's website."""


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
    # Validate site_name
    if site_name:
        invalid = [s for s in site_name if s not in VALID_SITES]
        if invalid:
            return json.dumps({
                "error": f"Invalid site(s): {invalid}. Valid options: {VALID_SITES}"
            })
    # Validate job_type
    if job_type and job_type not in VALID_JOB_TYPES:
        return json.dumps({
            "error": f"Invalid job_type: {job_type}. Valid options: {VALID_JOB_TYPES}"
        })
    # Validate description_format
    if description_format not in ("markdown", "html"):
        description_format = "markdown"
    # Cap results_wanted for responsible use
    if results_wanted > 50:
        results_wanted = 50

    try:
        import asyncio

        results = await asyncio.to_thread(
            _run_jobspy_search,
            search_term=search_term,
            location=location,
            site_name=site_name,
            distance=distance,
            job_type=job_type,
            is_remote=is_remote,
            results_wanted=results_wanted,
            hours_old=hours_old,
            country_indeed=country_indeed,
            linkedin_fetch_description=linkedin_fetch_description,
            linkedin_company_ids=linkedin_company_ids,
            google_search_term=google_search_term,
            easy_apply=easy_apply,
            enforce_annual_salary=enforce_annual_salary,
            offset=offset,
            description_format=description_format,
        )
        return json.dumps({
            "jobs": results,
            "total": len(results),
            "search_term": search_term,
            "status": "completed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }, default=str)
    except Exception as e:
        logger.error("Job search failed: %s", e)
        return json.dumps({"error": str(e), "status": "failed"})


@mcp.tool(description=EXTRACT_JOB_DESCRIPTION_DESCRIPTION)
async def extract_job_description(
    url: str,
    mode: str = "single",
    max_pages: int = 5,
) -> str:
    """Extract job description from a URL or crawl a careers page."""
    if not url.startswith(("http://", "https://")):
        return json.dumps({"error": "URL must include protocol (https://...)"})

    if mode not in ("single", "crawl"):
        return json.dumps({"error": "mode must be 'single' or 'crawl'"})

    if "linkedin.com" in url:
        return json.dumps({
            "error": "LinkedIn URLs are blocked by LinkedIn. Use search_jobs with "
                     "site_name=['linkedin'] and linkedin_fetch_description=true instead."
        })

    max_pages = min(max(int(max_pages), 1), 10)

    try:
        if mode == "single":
            result = await _extract_job_description(url)
        else:
            result = await _crawl_careers_page(url, max_pages)
        return json.dumps(result, default=str)
    except Exception as e:
        logger.error("Job description extraction failed: %s", e)
        return json.dumps({"error": str(e), "status": "failed"})


# ── Entry point ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run(transport="stdio")
