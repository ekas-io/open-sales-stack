"""Quick test script to validate techstack-intel against a real URL."""

import asyncio
import json
import sys
import os

# Add package to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.analyzer import analyze


async def main():
    url = sys.argv[1] if len(sys.argv) > 1 else "https://ekas.io"
    print(f"Scanning: {url}\n")

    report = await analyze(url)

    # Print summary
    print(report.summary())

    # Print full JSON
    print("\n--- Full JSON Report ---\n")
    print(json.dumps(report.to_dict(), indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
