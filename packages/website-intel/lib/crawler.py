"""Shared crawl4ai extraction client for website-intel."""

import contextlib
import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, LLMConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy

logger = logging.getLogger("website-intel")

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
        browser_config = BrowserConfig(headless=True, verbose=False)
        _crawler = AsyncWebCrawler(config=browser_config)
        with _suppress_stdout():
            await _crawler.__aenter__()
    return _crawler


def _build_extraction_strategy(prompt: str, schema: dict[str, Any]) -> LLMExtractionStrategy:
    """Build an LLMExtractionStrategy for the given prompt and schema."""
    return LLMExtractionStrategy(
        llm_config=LLMConfig(provider=LLM_PROVIDER, api_token=LLM_API_KEY),
        instruction=prompt,
        schema=schema,
    )


def _build_run_config(
    prompt: str,
    schema: dict[str, Any],
    mode: str,
    limit: int,
    input_format: str,
) -> CrawlerRunConfig:
    """Build a CrawlerRunConfig with LLM extraction strategy."""
    extraction = LLMExtractionStrategy(
        llm_config=LLMConfig(provider=LLM_PROVIDER, api_token=LLM_API_KEY),
        instruction=prompt,
        schema=schema,
        input_format=input_format,
    )
    kwargs: dict[str, Any] = {"extraction_strategy": extraction, "verbose": False, "page_timeout": 600000}
    if mode == "crawl":
        kwargs["deep_crawl_strategy"] = BFSDeepCrawlStrategy(
            max_depth=2, max_pages=limit, include_external=False,
        )
    return CrawlerRunConfig(**kwargs)


def _parse_results(results: list, mode: str) -> Any:
    """Parse crawl4ai results into clean output."""
    extracted = []
    for r in results:
        if not r.success or not r.extracted_content:
            continue
        parsed: Any = r.extracted_content
        if isinstance(parsed, str):
            try:
                parsed = json.loads(parsed)
            except (json.JSONDecodeError, ValueError):
                logger.warning("Could not parse extracted_content as JSON for %s", r.url)
        if isinstance(parsed, list) and len(parsed) == 1:
            parsed = parsed[0]
        extracted.append(parsed)

    if mode == "scrape" and len(extracted) == 1:
        return extracted[0]
    return extracted


def _has_data(data: Any) -> bool:
    """Check if extraction yielded usable data."""
    if data is None:
        return False
    if isinstance(data, (list, dict)) and len(data) == 0:
        return False
    return True


async def _run_extraction(
    url: str, prompt: str, schema: dict[str, Any], mode: str, limit: int, input_format: str,
) -> Any:
    """Run crawl4ai extraction with the given input format."""
    config = _build_run_config(prompt, schema, mode, limit, input_format)
    crawler = await get_crawler()
    with _suppress_stdout():
        result = await crawler.arun(url=url, config=config)

    results = result if isinstance(result, list) else [result]
    if not results:
        raise RuntimeError("crawl4ai returned no results for the given URL")

    failed = [r for r in results if not r.success]
    if failed and len(failed) == len(results):
        error_msg = getattr(failed[0], "error_message", "unknown error")
        raise RuntimeError(f"crawl4ai extraction failed: {error_msg}")

    return _parse_results(results, mode)


async def extract(
    url: str,
    prompt: str,
    schema: dict[str, Any],
    mode: str = "scrape",
    limit: int = 5,
) -> dict[str, Any]:
    """Extract structured data from a URL.

    Tries markdown first (cheaper on tokens), falls back to HTML if needed.
    """
    logger.info("Starting extraction: url=%s mode=%s", url, mode)

    data = await _run_extraction(url, prompt, schema, mode, limit, "markdown")
    if _has_data(data):
        logger.info("Extraction completed (markdown): url=%s", url)
        return {"data": data, "status": "completed", "timestamp": datetime.now(timezone.utc).isoformat()}

    logger.info("Markdown returned empty, retrying with HTML: url=%s", url)
    data = await _run_extraction(url, prompt, schema, mode, limit, "html")
    logger.info("Extraction completed (html fallback): url=%s", url)
    return {"data": data, "status": "completed", "timestamp": datetime.now(timezone.utc).isoformat()}
