"""Shared crawl4ai browser client for hiring-intel."""

from datetime import datetime, timezone

_crawler = None


async def get_crawler():
    """Lazily initialize a shared headless browser instance."""
    global _crawler
    if _crawler is None:
        from crawl4ai import AsyncWebCrawler, BrowserConfig

        _crawler = AsyncWebCrawler(config=BrowserConfig(headless=True))
        await _crawler.__aenter__()
    return _crawler


async def fetch_single_page(url: str) -> dict:
    """Fetch a single URL and return its markdown content."""
    from crawl4ai import CrawlerRunConfig

    crawler = await get_crawler()
    config = CrawlerRunConfig(wait_until="networkidle", page_timeout=20000)
    result = await crawler.arun(url=url, config=config)

    if not result.success:
        error_msg = getattr(result, "error_message", "unknown error")
        raise RuntimeError(f"Failed to fetch page: {error_msg}")

    return {
        "url": url,
        "markdown": result.markdown if result.markdown else None,
        "status": "completed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def crawl_careers_page(url: str, max_pages: int) -> dict:
    """Crawl a company careers page to discover job listings."""
    from crawl4ai import CrawlerRunConfig
    from crawl4ai.deep_crawling import BFSDeepCrawlStrategy

    crawler = await get_crawler()
    config = CrawlerRunConfig(
        wait_until="networkidle",
        page_timeout=20000,
        deep_crawl_strategy=BFSDeepCrawlStrategy(
            max_depth=2,
            max_pages=max_pages,
            include_external=False,
        ),
    )
    result = await crawler.arun(url=url, config=config)
    results = result if isinstance(result, list) else [result]

    pages = [
        {"url": r.url, "markdown": r.markdown if r.markdown else None}
        for r in results
        if r.success
    ]

    return {
        "careers_url": url,
        "pages_found": len(pages),
        "pages": pages,
        "status": "completed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
