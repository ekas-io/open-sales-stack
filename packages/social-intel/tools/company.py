"""LinkedIn company scrape tool for social-intel."""

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


async def scrape_linkedin_company(linkedin_url: str) -> str:
    """Scrape a LinkedIn company page and return structured JSON."""
    from linkedin_scraper import CompanyScraper

    browser = None
    try:
        browser = await get_authenticated_browser()
        scraper = CompanyScraper(browser.page)
        company = await scraper.scrape(linkedin_url)
        return json.dumps(_serialize(company), indent=2, default=str)
    except Exception as e:
        logger.error("Company scrape failed for %s: %s", linkedin_url, e)
        return json.dumps({"error": str(e), "status": "failed"})
    finally:
        if browser:
            await browser.close()
