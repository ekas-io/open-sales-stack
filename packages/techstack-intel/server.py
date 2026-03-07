"""
techstack-intel MCP server.

Detects technologies used by a company from their website.
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

mcp = FastMCP("open-sales-stack-techstack-intel")


@mcp.tool()
async def detect_techstack(url: str) -> str:
    """Detect the technology stack used by a company website. Coming soon."""
    return json.dumps({"error": "techstack-intel is not yet implemented"})


if __name__ == "__main__":
    mcp.run(transport="stdio")
