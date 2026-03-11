"""LinkedIn profile scrape tool for social-intel."""

import json
import logging

from lib.browser import get_authenticated_browser

logger = logging.getLogger("social-intel")


def _serialize(obj) -> dict:
    """Serialize a pydantic model or dict to a plain dict."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    return obj


async def scrape_linkedin_profile(linkedin_url: str) -> str:
    """Scrape a LinkedIn profile and return structured JSON."""
    from linkedin_scraper import PersonScraper

    browser = None
    try:
        browser = await get_authenticated_browser()
        scraper = PersonScraper(browser.page)
        person = await scraper.scrape(linkedin_url)
        return json.dumps(_serialize(person), indent=2, default=str)
    except Exception as e:
        logger.error("Profile scrape failed for %s: %s", linkedin_url, e)
        return json.dumps({"error": str(e), "status": "failed"})
    finally:
        if browser:
            await browser.close()
