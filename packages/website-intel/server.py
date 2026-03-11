"""
website-intel MCP server.

Scrapes websites and extracts structured data using crawl4ai with LLM extraction.
"""

import logging
import os
import sys

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# ── Environment ──────────────────────────────────────────────────────────

_pkg_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.dirname(os.path.dirname(_pkg_dir))

if _pkg_dir not in sys.path:
    sys.path.insert(0, _pkg_dir)

load_dotenv(os.path.join(_pkg_dir, ".env"))
load_dotenv(os.path.join(_root_dir, ".env"))

LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openai/gpt-5-mini-2025-08-07")

if not LLM_API_KEY or LLM_API_KEY.startswith("your-"):
    print(
        "Error: LLM_API_KEY is required. Run bash scripts/setup.sh or set it in .env",
        file=sys.stderr,
    )
    sys.exit(1)

# ── Logging ──────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("website-intel")

# ── MCP Server ───────────────────────────────────────────────────────────

mcp = FastMCP("open-sales-stack-website-intel")

TOOL_DESCRIPTION = """\
Scrape or crawl a webpage and extract structured data as JSON using a custom schema. \
Use this tool when you know the specific URL of a website and need to extract \
particular information in a well-defined, structured format.

Two modes are available:
  \u2022 'scrape' (default) \u2014 single-page extraction with full JS rendering.
  \u2022 'crawl' \u2014 multi-page extraction that follows links up to a page limit.

You MUST provide three things:
  1. The target URL
  2. A JSON Schema object defining the exact shape of the data you want returned
  3. A natural-language prompt describing what to extract"""


@mcp.tool(description=TOOL_DESCRIPTION)
async def website_intel_extract(
    url: str,
    schema: dict,
    prompt: str,
    mode: str = "scrape",
    limit: int = 5,
) -> str:
    """Scrape or crawl a webpage and extract structured data as JSON."""
    from tools.extract import website_intel_extract as _extract

    return await _extract(url, schema, prompt, mode, limit)


# ── Entry point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run(transport="stdio")
