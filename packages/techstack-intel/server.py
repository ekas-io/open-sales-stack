"""
techstack-intel MCP server.

Detects technologies used by a company from their website.
"""

import logging
import os
import sys
from typing import Annotated

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from pydantic import Field

# ── Environment ──────────────────────────────────────────────────────────

_pkg_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.dirname(os.path.dirname(_pkg_dir))

if _pkg_dir not in sys.path:
    sys.path.insert(0, _pkg_dir)

load_dotenv(os.path.join(_pkg_dir, ".env"))
load_dotenv(os.path.join(_root_dir, ".env"))

# ── Logging ──────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("techstack-intel")

# ── MCP Server ───────────────────────────────────────────────────────────

mcp = FastMCP("open-sales-stack-techstack-intel")

TOOL_DESCRIPTION = """\
Detect the technology stack used by a company website. \
Takes a single URL and returns a comprehensive report of all technologies, \
services, and infrastructure detected.

Analyzes:
  - HTTP response headers (web server, framework, CDN, hosting)
  - HTML/DOM (CMS, JS frameworks, analytics, chat widgets, marketing tools)
  - DNS records (email provider, DNS provider, hosted services)
  - SSL certificates (certificate authority)
  - robots.txt & sitemap.xml (CMS, SEO tools)
  - Cookies (analytics, marketing, session technology)
  - Favicon fingerprinting

Returns a structured JSON report with each technology's name, category, \
confidence score (0-1), and evidence trail."""


@mcp.tool(description=TOOL_DESCRIPTION)
async def detect_techstack(
    url: Annotated[str, Field(
        description="URL of the company website to analyze. The `https://` prefix is added automatically if omitted.\n\nExample: `https://stripe.com`; `notion.so`",
    )],
) -> str:
    """Detect the technology stack used by a company website."""
    from tools.detect_techstack import detect_techstack as _detect

    return await _detect(url)


# ── Entry point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run(transport="stdio")
