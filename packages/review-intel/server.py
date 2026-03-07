"""
review-intel MCP server.

Extracts review data from G2, Capterra, Glassdoor, etc.
TODO: Implement — see packages/website-intel/server.py for reference.
"""

import json
import os

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

_pkg_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.dirname(os.path.dirname(_pkg_dir))
load_dotenv(os.path.join(_pkg_dir, ".env"))
load_dotenv(os.path.join(_root_dir, ".env"))

mcp = FastMCP("open-sales-stack-review-intel")


@mcp.tool()
async def get_reviews(company: str, platform: str = "g2") -> str:
    """Get review data for a company from review platforms. Coming soon."""
    return json.dumps({"error": "review-intel is not yet implemented"})


if __name__ == "__main__":
    mcp.run(transport="stdio")
