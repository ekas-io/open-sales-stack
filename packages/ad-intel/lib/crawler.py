"""
Shared crawl4ai extraction client.

Uses crawl4ai as a Python package (same pattern as website-intel) for
structured data extraction with LLM-powered strategies.
"""

import json
import logging
import os
from typing import Any

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, LLMConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy

logger = logging.getLogger("ad-intel")

# ── Shared crawler instance ─────────────────────────────────────────────

_crawler: AsyncWebCrawler | None = None


async def get_crawler() -> AsyncWebCrawler:
    """Lazily initialize a shared browser instance."""
    global _crawler
    if _crawler is None:
        browser_config = BrowserConfig(headless=True)
        _crawler = AsyncWebCrawler(config=browser_config)
        await _crawler.__aenter__()
    return _crawler


# ── Extraction logic ────────────────────────────────────────────────────


def _build_run_config(
    prompt: str,
    schema: dict[str, Any],
    input_format: str,
    delay_before_return_html: int = 5,
) -> CrawlerRunConfig:
    """Build a CrawlerRunConfig with LLM extraction strategy."""
    openai_api_key = os.environ.get("OPENAI_API_KEY", "")
    llm_provider = os.environ.get("LLM_PROVIDER", "openai/gpt-4o-mini")

    extraction = LLMExtractionStrategy(
        llm_config=LLMConfig(provider=llm_provider, api_token=openai_api_key),
        instruction=prompt,
        schema=schema,
        input_format=input_format,
    )

    return CrawlerRunConfig(
        extraction_strategy=extraction,
        delay_before_return_html=delay_before_return_html,
        page_timeout=60000,
        magic=True,
    )


def _parse_result(result: Any) -> Any:
    """Parse crawl4ai result into clean output.

    crawl4ai may chunk large pages and return a list of extraction results.
    When multiple chunks are returned, merge them by combining ads arrays
    and keeping the first chunk's metadata (total_result_count, etc.).
    """
    if not result.success or not result.extracted_content:
        return None

    parsed = result.extracted_content
    if isinstance(parsed, str):
        try:
            parsed = json.loads(parsed)
        except (json.JSONDecodeError, ValueError):
            logger.warning("Could not parse extracted_content as JSON for %s", result.url)
            return None

    # Unwrap single-element arrays
    if isinstance(parsed, list) and len(parsed) == 1:
        parsed = parsed[0]
    elif isinstance(parsed, list) and len(parsed) > 1:
        # Merge multiple chunks: combine ads arrays, keep first chunk's metadata
        merged = dict(parsed[0]) if isinstance(parsed[0], dict) else {}
        if "ads" in merged:
            for chunk in parsed[1:]:
                if isinstance(chunk, dict) and "ads" in chunk:
                    merged["ads"].extend(chunk["ads"])
            parsed = merged
        else:
            # Non-ad-library data — just return first chunk
            parsed = parsed[0] if isinstance(parsed[0], dict) else parsed

    return parsed


async def extract_structured_data(
    url: str,
    prompt: str,
    schema: dict,
    mode: str = "scrape",
    limit: int = 5,
    wait_for: str | None = None,
    delay_before_return_html: int = 5,
) -> dict:
    """
    Extract structured data from a URL using crawl4ai.

    Tries markdown input first (cheaper on tokens), falls back to HTML
    if markdown returns empty data.

    Args:
        url: Target URL to scrape.
        prompt: Natural language instruction for what to extract.
        schema: JSON Schema defining the shape of data to return.
        mode: "scrape" for single-page (only mode currently used).
        limit: Max pages for crawl mode (reserved for future use).
        wait_for: CSS selector to wait for before extraction (unused with magic=True).
        delay_before_return_html: Seconds to wait for JS rendering.

    Returns:
        Parsed extracted data dict.
    """
    logger.info("Starting extraction: url=%s mode=%s", url, mode)
    crawler = await get_crawler()

    # Try markdown first (cheaper on tokens)
    config = _build_run_config(prompt, schema, "markdown", delay_before_return_html)
    result = await crawler.arun(url=url, config=config)

    if not result.success:
        error_msg = getattr(result, "error_message", "unknown error")
        raise RuntimeError(f"crawl4ai extraction failed: {error_msg}")

    data = _parse_result(result)

    if data:
        logger.info("Extraction completed (markdown): url=%s", url)
        return data

    # Fall back to HTML for JS-heavy SPAs
    logger.info("Markdown returned empty, retrying with HTML: url=%s", url)
    config = _build_run_config(prompt, schema, "html", delay_before_return_html)
    result = await crawler.arun(url=url, config=config)

    if not result.success:
        error_msg = getattr(result, "error_message", "unknown error")
        raise RuntimeError(f"crawl4ai HTML fallback failed: {error_msg}")

    data = _parse_result(result)
    logger.info("Extraction completed (html fallback): url=%s", url)

    return data or {}
