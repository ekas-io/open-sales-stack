"""
hiring-intel MCP server.

Finds job postings from company careers pages and ATS platforms.
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

mcp = FastMCP("open-sales-stack-hiring-intel")


@mcp.tool()
async def find_job_postings(company: str, url: str = "") -> str:
    """Find job postings for a company from careers pages and ATS platforms. Coming soon."""
    return json.dumps({"error": "hiring-intel is not yet implemented"})


if __name__ == "__main__":
    mcp.run(transport="stdio")
