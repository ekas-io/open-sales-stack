"""
social-finder MCP server.

Finds social profiles (LinkedIn, Twitter, GitHub) for people and companies.
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

mcp = FastMCP("open-sales-stack-social-finder")


@mcp.tool()
async def find_social_profiles(name: str, company: str = "") -> str:
    """Find social media profiles for a person or company. Coming soon."""
    return json.dumps({"error": "social-finder is not yet implemented"})


if __name__ == "__main__":
    mcp.run(transport="stdio")
