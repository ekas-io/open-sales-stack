"""
website-intel MCP server.

Scrapes websites and extracts structured data using crawl4ai with LLM extraction.
Run directly: python packages/website-intel/server.py
"""

import asyncio
import contextlib
import io
import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, LLMConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy

# ── Environment ──────────────────────────────────────────────────────────

# Load .env from package directory first, then root as fallback
_pkg_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.dirname(os.path.dirname(_pkg_dir))

load_dotenv(os.path.join(_pkg_dir, ".env"))
load_dotenv(os.path.join(_root_dir, ".env"))

LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openai/gpt-4o-mini")

if not LLM_API_KEY or LLM_API_KEY.startswith("your-"):
    print("Error: LLM_API_KEY is required. Run bash scripts/setup.sh or set it in .env", file=sys.stderr)
    sys.exit(1)

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openai/gpt-5-mini-2025-08-07")

# ── Logging ──────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stderr,  # Keep stdout clean for MCP JSON-RPC
)
logger = logging.getLogger("website-intel")

# ── Shared crawler instance ─────────────────────────────────────────────

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
    """Lazily initialize a shared browser instance."""
    global _crawler
    if _crawler is None:
        browser_config = BrowserConfig(headless=True, verbose=False)
        _crawler = AsyncWebCrawler(config=browser_config)
        with _suppress_stdout():
            await _crawler.__aenter__()
    return _crawler


# ── Extraction logic ────────────────────────────────────────────────────


def _build_run_config(
    prompt: str,
    schema: dict[str, Any],
    mode: str,
    limit: int,
    input_format: str,
) -> CrawlerRunConfig:
    """Build a CrawlerRunConfig with LLM extraction strategy."""
    extraction = LLMExtractionStrategy(
        llm_config=LLMConfig(
            provider=LLM_PROVIDER,
            api_token=LLM_API_KEY,
        ),
        instruction=prompt,
        schema=schema,
        input_format=input_format,
    )

    kwargs: dict[str, Any] = {"extraction_strategy": extraction, "verbose": False}

    if mode == "crawl":
        kwargs["deep_crawl_strategy"] = BFSDeepCrawlStrategy(
            max_depth=2,
            max_pages=limit,
            include_external=False,
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
        # Unwrap single-element arrays
        if isinstance(parsed, list) and len(parsed) == 1:
            parsed = parsed[0]
        extracted.append(parsed)

    # For single-page scrape, return first result directly
    if mode == "scrape" and len(extracted) == 1:
        return extracted[0]
    return extracted


def _has_data(data: Any) -> bool:
    """Check if extraction yielded usable data."""
    if data is None:
        return False
    if isinstance(data, list) and len(data) == 0:
        return False
    if isinstance(data, dict) and len(data) == 0:
        return False
    return True


async def _run_extraction(
    url: str,
    prompt: str,
    schema: dict[str, Any],
    mode: str,
    limit: int,
    input_format: str,
) -> Any:
    """Run crawl4ai extraction with given input format."""
    config = _build_run_config(prompt, schema, mode, limit, input_format)
    crawler = await get_crawler()
    with _suppress_stdout():
        result = await crawler.arun(url=url, config=config)

    # Deep crawl returns a list
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
    """
    Extract structured data from a URL.

    Tries markdown input first (cheaper on tokens), falls back to HTML
    if markdown returns empty data.
    """
    logger.info("Starting extraction: url=%s mode=%s", url, mode)

    # Try markdown first
    data = await _run_extraction(url, prompt, schema, mode, limit, "markdown")

    if _has_data(data):
        logger.info("Extraction completed (markdown): url=%s", url)
        return {
            "data": data,
            "status": "completed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # Fall back to HTML for JS-heavy SPAs
    logger.info("Markdown returned empty, retrying with HTML: url=%s", url)
    data = await _run_extraction(url, prompt, schema, mode, limit, "html")

    logger.info("Extraction completed (html fallback): url=%s", url)
    return {
        "data": data,
        "status": "completed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── MCP Server ──────────────────────────────────────────────────────────

mcp = FastMCP("open-sales-stack-website-intel")

TOOL_DESCRIPTION = """\
Scrape or crawl a webpage and extract structured data as JSON using a custom schema. \
Use this tool when you know the specific URL of a website and need to extract \
particular information in a well-defined, structured format. \

Two modes are available:
  \u2022 'scrape' (default) \u2014 single-page extraction with full JS rendering. Fast, reliable, \
handles JavaScript-heavy SPAs and sites that require browser rendering.
  \u2022 'crawl' \u2014 multi-page extraction that follows links up to a page limit. \
Use when data spans multiple pages (paginated lists, multi-page docs).

Common use-cases:
  \u2022 Extract pricing tiers and plans from a SaaS pricing page (scrape)
  \u2022 Extract review data from G2, Capterra, etc. (scrape)
  \u2022 Extract team member profiles, names, roles, and contact details (scrape)
  \u2022 Extract product feature comparisons or specification tables (scrape)
  \u2022 Gather data from multi-page documentation or blog archives (crawl)
  \u2022 Extract job listings across paginated results (crawl)

You MUST provide three things:
  1. The target URL
  2. A JSON Schema object defining the exact shape of the data you want returned \
(see the 'schema' parameter description for full examples)
  3. A natural-language prompt describing what to extract"""

SCHEMA_DESCRIPTION = """\
A valid JSON Schema object that defines the exact structure of the data you want extracted. \
The returned JSON will match your specification exactly. The root must be an object with \
'type', 'properties', and optionally 'required'. \
Use standard JSON Schema types: 'string', 'number', 'boolean', 'array', 'object'. \

Example \u2014 extract pricing tiers:
{
  "type": "object",
  "required": [],
  "properties": {
    "pricing_tiers": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "tier_name": { "type": "string" },
          "price": { "type": "string" },
          "features": { "type": "array", "items": { "type": "string" } }
        }
      }
    }
  }
}

Example \u2014 extract team/contact info:
{
  "type": "object",
  "properties": {
    "team_members": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "role": { "type": "string" },
          "email": { "type": "string" }
        }
      }
    }
  }
}"""


@mcp.tool(description=TOOL_DESCRIPTION)
async def website_intel_extract(
    url: str,
    schema: dict,
    prompt: str,
    mode: str = "scrape",
    limit: int = 5,
) -> str:
    """Scrape or crawl a webpage and extract structured data as JSON."""
    # Validate inputs
    if not url.startswith(("http://", "https://")):
        return json.dumps({"error": "URL must include protocol (https://...)"})

    if mode not in ("scrape", "crawl"):
        return json.dumps({"error": "mode must be 'scrape' or 'crawl'"})

    if not isinstance(limit, int) or limit < 1 or limit > 10:
        limit = min(max(int(limit), 1), 10)

    try:
        result = await extract(url, prompt, schema, mode, limit)
        return json.dumps(result, default=str)
    except Exception as e:
        logger.error("Extraction failed: %s", e)
        return json.dumps({"error": str(e), "status": "failed"})


# ── Entry point ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run(transport="stdio")
