"""
Shared crawl4ai extraction client.

Uses crawl4ai as a Python package (same pattern as website-intel) for
structured data extraction with LLM-powered strategies.
"""

import contextlib
import json
import logging
import os
import sys
from typing import Any

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, LLMConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy

logger = logging.getLogger("ad-intel")

LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openai/gpt-5-mini-2025-08-07")

_crawler: AsyncWebCrawler | None = None


@contextlib.contextmanager
def _suppress_stdout():
    """Redirect stdout to stderr so crawl4ai prints don't break MCP JSON-RPC."""
    old_stdout = sys.stdout
    sys.stdout = sys.stderr
    try:
        yield
    finally:
        sys.stdout = old_stdout


async def get_crawler() -> AsyncWebCrawler:
    """Lazily initialize a shared headless browser instance."""
    global _crawler
    if _crawler is None:
        browser_config = BrowserConfig(headless=True, verbose=False, extra_args=["--ignore-certificate-errors"])
        _crawler = AsyncWebCrawler(config=browser_config)
        with _suppress_stdout():
            await _crawler.__aenter__()
    return _crawler


# ── Extraction logic ────────────────────────────────────────────────────


def _build_run_config(
    prompt: str,
    schema: dict[str, Any],
    input_format: str,
) -> CrawlerRunConfig:
    """Build a CrawlerRunConfig with LLM extraction strategy."""
    extraction = LLMExtractionStrategy(
        llm_config=LLMConfig(provider=LLM_PROVIDER, api_token=LLM_API_KEY),
        instruction=prompt,
        schema=schema,
        input_format=input_format,
    )

    return CrawlerRunConfig(
        extraction_strategy=extraction,
        verbose=False,
        page_timeout=60000,
    )


def _parse_result(result: Any) -> Any:
    """Parse crawl4ai result into clean output.

    crawl4ai may chunk large pages and return a list of extraction results.
    When multiple chunks are returned, merge them by combining arrays
    and keeping the first chunk's metadata.
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
        # Multiple chunks — just return first chunk
        parsed = parsed[0] if isinstance(parsed[0], dict) else parsed

    return parsed


def _has_data(data: Any) -> bool:
    """Check if extraction yielded usable data."""
    if data is None:
        return False
    if isinstance(data, (list, dict)) and len(data) == 0:
        return False
    return True


async def fetch_markdown(url: str, delay_before_return_html: int = 3) -> str:
    """Fetch a page and return its markdown without LLM extraction."""
    config = CrawlerRunConfig(
        delay_before_return_html=delay_before_return_html,
        page_timeout=60000,
        verbose=False,
    )
    crawler = await get_crawler()
    with _suppress_stdout():
        result = await crawler.arun(url=url, config=config)
    if not result.success:
        return ""
    return result.markdown or ""


async def extract_structured_data(
    url: str,
    prompt: str,
    schema: dict,
    mode: str = "scrape",
    input_format: str = "markdown",
) -> dict:
    """
    Extract structured data from a URL using crawl4ai.

    By default uses HTML input. Set input_format="markdown" to try markdown
    first (cheaper on tokens) with HTML fallback.

    Args:
        url: Target URL to scrape.
        prompt: Natural language instruction for what to extract.
        schema: JSON Schema defining the shape of data to return.
        mode: "scrape" for single-page (only mode currently used).
        limit: Max pages for crawl mode (reserved for future use).
        input_format: "html" (default) or "markdown" (with HTML fallback).

    Returns:
        Parsed extracted data dict.
    """
    logger.info("Starting extraction: url=%s mode=%s format=%s", url, mode, input_format)

    crawler = await get_crawler()

    if input_format == "markdown":
        # Try markdown first (cheaper on tokens)
        config = _build_run_config(prompt, schema, "markdown")
        with _suppress_stdout():
            result = await crawler.arun(url=url, config=config)

        if not result.success:
            error_msg = getattr(result, "error_message", "unknown error")
            raise RuntimeError(f"crawl4ai extraction failed: {error_msg}")

        data = _parse_result(result)

        if _has_data(data):
            logger.info("Extraction completed (markdown): url=%s", url)
            return data

        logger.info("Markdown returned empty, retrying with HTML: url=%s", url)

    # HTML extraction (direct or fallback)
    config = _build_run_config(prompt, schema, "html")
    with _suppress_stdout():
        result = await crawler.arun(url=url, config=config)

    if not result.success:
        error_msg = getattr(result, "error_message", "unknown error")
        raise RuntimeError(f"crawl4ai HTML extraction failed: {error_msg}")

    data = _parse_result(result)
    logger.info("Extraction completed (html): url=%s", url)

    return data or {}
