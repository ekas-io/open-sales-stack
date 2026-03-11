"""
review-intel MCP server.

Extracts review data from G2, Capterra, Glassdoor, etc.
TODO: Implement — see packages/website-intel/server.py for reference.
"""

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

# ── MCP Server ───────────────────────────────────────────────────────────

mcp = FastMCP("open-sales-stack-review-intel")


@mcp.tool()
async def get_reviews(company: str, platform: str = "g2") -> str:
    """Get review data for a company from review platforms. Coming soon."""
    from tools.get_reviews import get_reviews as _get

    return await _get(company, platform)


# ── Entry point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run(transport="stdio")
