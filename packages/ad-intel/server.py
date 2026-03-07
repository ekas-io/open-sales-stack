"""
ad-intel MCP server.

Finds active ad campaigns from LinkedIn Ad Library and Meta Ad Library.
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

mcp = FastMCP("open-sales-stack-ad-intel")


@mcp.tool()
async def find_ads(company: str, platform: str = "linkedin") -> str:
    """Find active ad campaigns for a company. Coming soon."""
    return json.dumps({"error": "ad-intel is not yet implemented"})


if __name__ == "__main__":
    mcp.run(transport="stdio")
