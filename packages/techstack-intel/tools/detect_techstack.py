"""Tech stack detection tool for techstack-intel."""

import json
import logging

from lib.analyzer import analyze

logger = logging.getLogger("techstack-intel")


async def detect_techstack(url: str) -> str:
    """Detect the technology stack used by a company website."""
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    try:
        report = await analyze(url)
        return json.dumps(report.to_dict(), indent=2, default=str)
    except Exception as e:
        logger.error("Analysis failed for %s: %s", url, e)
        return json.dumps({"error": str(e), "status": "failed"})
