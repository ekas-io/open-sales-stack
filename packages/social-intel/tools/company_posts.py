"""LinkedIn company posts scrape tool for social-intel."""

import json
import logging

from lib.browser import get_authenticated_browser

logger = logging.getLogger("social-intel")


def _serialize(obj) -> dict | list:
    """Serialize a pydantic model or list of models to plain Python objects."""
    if isinstance(obj, list):
        return [_serialize(item) for item in obj]
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    return obj


async def scrape_linkedin_company_posts(linkedin_url: str) -> str:
    """Scrape recent posts from a LinkedIn company page and return JSON."""
    from linkedin_scraper import CompanyPostsScraper

    browser = None
    try:
        browser = await get_authenticated_browser()
        scraper = CompanyPostsScraper(browser.page)
        posts = await scraper.scrape(linkedin_url)
        return json.dumps(_serialize(posts), indent=2, default=str)
    except Exception as e:
        logger.error("Company posts scrape failed for %s: %s", linkedin_url, e)
        return json.dumps({"error": str(e), "status": "failed"})
    finally:
        if browser:
            await browser.close()
