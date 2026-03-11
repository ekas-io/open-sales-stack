"""Job description extraction tool for hiring-intel."""

import json
import logging

from lib.crawler import fetch_single_page, crawl_careers_page

logger = logging.getLogger("hiring-intel")


def _validate_extract_params(url: str, mode: str) -> str | None:
    """Validate extraction parameters. Returns an error JSON string or None."""
    if not url.startswith(("http://", "https://")):
        return json.dumps({"error": "URL must include protocol (https://...)"})
    if mode not in ("single", "crawl"):
        return json.dumps({"error": "mode must be 'single' or 'crawl'"})
    if "linkedin.com" in url:
        return json.dumps({
            "error": (
                "LinkedIn URLs are blocked. Use search_jobs with "
                "site_name=['linkedin'] and linkedin_fetch_description=true instead."
            )
        })
    return None


async def extract_job_description(url: str, mode: str = "single", max_pages: int = 5) -> str:
    """Extract a job description from a URL or crawl a careers page."""
    error = _validate_extract_params(url, mode)
    if error:
        return error

    max_pages = min(max(int(max_pages), 1), 10)

    try:
        if mode == "single":
            result = await fetch_single_page(url)
        else:
            result = await crawl_careers_page(url, max_pages)
        return json.dumps(result, default=str)
    except Exception as e:
        logger.error("Job description extraction failed: %s", e)
        return json.dumps({"error": str(e), "status": "failed"})
