"""
social-intel MCP server.

Scrapes LinkedIn profiles, companies, and company posts using linkedin_scraper v3.0+.
Run directly: python packages/social-intel/server.py
"""

import json
import logging
import os
import subprocess
import sys

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# ── Environment ──────────────────────────────────────────────────────────

_pkg_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.dirname(os.path.dirname(_pkg_dir))

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


def _ensure_dependencies():
    """Check and install linkedin-scraper and playwright if missing."""
    try:
        import linkedin_scraper  # noqa: F401

        logger.info("linkedin-scraper is installed")
    except ImportError:
        logger.info("linkedin-scraper not found, installing...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "linkedin-scraper>=3.0"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        logger.info("linkedin-scraper installed successfully")

    # Ensure playwright browsers are installed
    try:
        subprocess.check_call(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        logger.warning("Failed to install playwright chromium browser")


_ensure_dependencies()

# ── Session management ───────────────────────────────────────────────────

SESSION_FILE = os.path.join(_pkg_dir, "linkedin_session.json")


async def _get_authenticated_browser():
    """Create an authenticated BrowserManager instance.

    Login strategy:
    - If a saved session exists, reuse it.
    - If LINKEDIN_EMAIL and LINKEDIN_PASSWORD env vars are set, use programmatic login.
    - Otherwise, open a visible browser for manual login.
    """
    from linkedin_scraper import BrowserManager

    has_session = os.path.exists(SESSION_FILE)
    email = os.getenv("LINKEDIN_EMAIL", "")
    password = os.getenv("LINKEDIN_PASSWORD", "")
    has_credentials = bool(email and password)

    if has_session:
        logger.info("Reusing saved LinkedIn session")
        browser = BrowserManager(headless=True)
        await browser.start()
        await browser.load_session(SESSION_FILE)
        return browser

    if has_credentials:
        logger.info("Logging in with LINKEDIN_EMAIL / LINKEDIN_PASSWORD")
        from linkedin_scraper import login_with_credentials

        browser = BrowserManager(headless=True)
        await browser.start()
        await login_with_credentials(browser.page, email=email, password=password)
        await browser.save_session(SESSION_FILE)
        return browser

    # Manual login fallback
    logger.info("No credentials found — opening browser for manual login")
    from linkedin_scraper import wait_for_manual_login

    browser = BrowserManager(headless=False)
    await browser.start()
    await browser.page.goto("https://www.linkedin.com/login")
    await wait_for_manual_login(browser.page, timeout=300000)
    await browser.save_session(SESSION_FILE)
    return browser


# ── MCP Server ───────────────────────────────────────────────────────────

mcp = FastMCP("open-sales-stack-social-intel")

# ── Tool 1: Profile scrape ──────────────────────────────────────────────

PROFILE_DESCRIPTION = """\
Scrape a LinkedIn profile and return structured data about the person.

Takes a LinkedIn profile URL (e.g. https://www.linkedin.com/in/username/)
and returns name, headline, location, about section, work experiences,
education, and skills.

Returns a JSON object with profile fields."""


@mcp.tool(description=PROFILE_DESCRIPTION)
async def scrape_linkedin_profile(linkedin_url: str) -> str:
    """Scrape a LinkedIn profile for structured person data."""
    from linkedin_scraper import PersonScraper

    browser = None
    try:
        browser = await _get_authenticated_browser()
        scraper = PersonScraper(browser.page)
        person = await scraper.scrape(linkedin_url)
        result = person.model_dump() if hasattr(person, "model_dump") else person.dict()
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        logger.error("Profile scrape failed for %s: %s", linkedin_url, e)
        return json.dumps({"error": str(e), "status": "failed"})
    finally:
        if browser:
            await browser.close()


# ── Tool 2: Company scrape ──────────────────────────────────────────────

COMPANY_DESCRIPTION = """\
Scrape a LinkedIn company page and return structured data.

Takes a LinkedIn company URL (e.g. https://www.linkedin.com/company/company-name/)
and returns company name, industry, company size, headquarters, founded year,
specialties, and overview.

Returns a JSON object with company fields."""


@mcp.tool(description=COMPANY_DESCRIPTION)
async def scrape_linkedin_company(linkedin_url: str) -> str:
    """Scrape a LinkedIn company page for structured company data."""
    from linkedin_scraper import CompanyScraper

    browser = None
    try:
        browser = await _get_authenticated_browser()
        scraper = CompanyScraper(browser.page)
        company = await scraper.scrape(linkedin_url)
        result = company.model_dump() if hasattr(company, "model_dump") else company.dict()
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        logger.error("Company scrape failed for %s: %s", linkedin_url, e)
        return json.dumps({"error": str(e), "status": "failed"})
    finally:
        if browser:
            await browser.close()


# ── Tool 3: Company posts ───────────────────────────────────────────────

COMPANY_POSTS_DESCRIPTION = """\
Scrape recent posts from a LinkedIn company page.

Takes a LinkedIn company URL (e.g. https://www.linkedin.com/company/company-name/)
and returns recent posts with text content, reaction counts, comment counts,
repost counts, and posted dates.

Returns a JSON array of post objects."""


@mcp.tool(description=COMPANY_POSTS_DESCRIPTION)
async def scrape_linkedin_company_posts(linkedin_url: str) -> str:
    """Scrape recent posts from a LinkedIn company page."""
    from linkedin_scraper import CompanyPostsScraper

    browser = None
    try:
        browser = await _get_authenticated_browser()
        scraper = CompanyPostsScraper(browser.page)
        posts = await scraper.scrape(linkedin_url)
        if isinstance(posts, list):
            result = [
                p.model_dump() if hasattr(p, "model_dump") else p.dict()
                for p in posts
            ]
        else:
            result = posts.model_dump() if hasattr(posts, "model_dump") else posts.dict()
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        logger.error("Company posts scrape failed for %s: %s", linkedin_url, e)
        return json.dumps({"error": str(e), "status": "failed"})
    finally:
        if browser:
            await browser.close()


if __name__ == "__main__":
    mcp.run(transport="stdio")
