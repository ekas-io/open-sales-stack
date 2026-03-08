"""
techstack-intel MCP server.

Detects technologies used by a company from their website.
Run directly: python packages/techstack-intel/server.py
"""

import json
import logging
import os
import sys

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# ── Environment ──────────────────────────────────────────────────────────

_pkg_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.dirname(os.path.dirname(_pkg_dir))

# Add package to Python path so techstack_intel is importable
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
async def detect_techstack(url: str) -> str:
    """Detect the technology stack used by a company website."""
    from techstack_intel.analyzer import analyze

    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    try:
        report = await analyze(url)
        return json.dumps(report.to_dict(), indent=2, default=str)
    except Exception as e:
        logger.error("Analysis failed for %s: %s", url, e)
        return json.dumps({"error": str(e), "status": "failed"})


if __name__ == "__main__":
    mcp.run(transport="stdio")
