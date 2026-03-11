"""
social-intel MCP server.

Scrapes LinkedIn profiles, companies, and company posts using linkedin_scraper v3.0+.
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
logger = logging.getLogger("social-intel")

# ── Dependency check ─────────────────────────────────────────────────────

from lib.browser import ensure_dependencies

ensure_dependencies()

# ── MCP Server ───────────────────────────────────────────────────────────

mcp = FastMCP("open-sales-stack-social-intel")

PROFILE_DESCRIPTION = """\
Scrape a LinkedIn profile and return structured data about the person.

Takes a LinkedIn profile URL (e.g. https://www.linkedin.com/in/username/)
and returns name, headline, location, about section, work experiences,
education, and skills."""

COMPANY_DESCRIPTION = """\
Scrape a LinkedIn company page and return structured data.

Takes a LinkedIn company URL (e.g. https://www.linkedin.com/company/company-name/)
and returns company name, industry, company size, headquarters, founded year,
specialties, and overview."""

COMPANY_POSTS_DESCRIPTION = """\
Scrape recent posts from a LinkedIn company page.

Takes a LinkedIn company URL (e.g. https://www.linkedin.com/company/company-name/)
and returns recent posts with text content, reaction counts, comment counts,
repost counts, and posted dates."""


@mcp.tool(description=PROFILE_DESCRIPTION)
async def scrape_linkedin_profile(linkedin_url: str) -> str:
    """Scrape a LinkedIn profile for structured person data."""
    from tools.profile import scrape_linkedin_profile as _scrape

    return await _scrape(linkedin_url)


@mcp.tool(description=COMPANY_DESCRIPTION)
async def scrape_linkedin_company(linkedin_url: str) -> str:
    """Scrape a LinkedIn company page for structured company data."""
    from tools.company import scrape_linkedin_company as _scrape

    return await _scrape(linkedin_url)


@mcp.tool(description=COMPANY_POSTS_DESCRIPTION)
async def scrape_linkedin_company_posts(linkedin_url: str) -> str:
    """Scrape recent posts from a LinkedIn company page."""
    from tools.company_posts import scrape_linkedin_company_posts as _scrape

    return await _scrape(linkedin_url)


# ── Entry point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run(transport="stdio")
