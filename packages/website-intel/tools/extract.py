"""Website extraction tool for website-intel."""

import json
import logging

from lib.crawler import extract

logger = logging.getLogger("website-intel")


def _validate_params(url: str, mode: str, limit: int) -> tuple[str | None, int]:
    """Validate tool parameters. Returns (error_json | None, clamped_limit)."""
    if not url.startswith(("http://", "https://")):
        return json.dumps({"error": "URL must include protocol (https://...)"}), limit
    if mode not in ("scrape", "crawl"):
        return json.dumps({"error": "mode must be 'scrape' or 'crawl'"}), limit
    return None, min(max(int(limit), 1), 10)


async def website_intel_extract(
    url: str,
    schema: dict,
    prompt: str,
    mode: str = "scrape",
    limit: int = 5,
) -> str:
    """Scrape or crawl a webpage and extract structured data as JSON."""
    error, limit = _validate_params(url, mode, limit)
    if error:
        return error

    try:
        result = await extract(url, prompt, schema, mode, limit)
        return json.dumps(result, default=str)
    except Exception as e:
        logger.error("Extraction failed: %s", e)
        return json.dumps({"error": str(e), "status": "failed"})
