"""Build a DetectionTarget by fetching URL data, DNS records, SSL info, etc."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import re
import socket
import ssl
from urllib.parse import urlparse

import dns.resolver
import httpx

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

from lib.models import DetectionTarget
from lib.utils.helpers import (
    extract_domain,
    extract_inline_scripts,
    extract_link_tags,
    extract_meta_tags,
    extract_scripts,
    normalize_url,
)
from lib.signatures.database import CNAME_SUBDOMAINS

logger = logging.getLogger("techstack-intel.target_builder")

_crawler: AsyncWebCrawler | None = None


async def _get_crawler() -> AsyncWebCrawler:
    """Lazily initialize a shared browser instance."""
    global _crawler
    if _crawler is None:
        browser_config = BrowserConfig(headless=True)
        _crawler = AsyncWebCrawler(config=browser_config)
        await _crawler.__aenter__()
    return _crawler


async def _fetch_page(url: str) -> dict:
    """Fetch page with Crawl4AI headless browser. Returns raw data dict."""
    crawler = await _get_crawler()
    config = CrawlerRunConfig(
        wait_until="networkidle",
        page_timeout=15000,
    )
    result = await crawler.arun(url=url, config=config)

    if not result.success:
        error_msg = getattr(result, "error_message", "unknown error")
        raise RuntimeError(f"Page fetch failed: {error_msg}")

    # Extract cookies from the result
    cookies = []
    if hasattr(result, "cookies") and result.cookies:
        cookies = result.cookies if isinstance(result.cookies, list) else []

    # Get response headers
    headers = {}
    if hasattr(result, "response_headers") and result.response_headers:
        headers = {
            k.lower(): v
            for k, v in (result.response_headers or {}).items()
        }

    html = result.html or ""

    return {
        "html": html,
        "final_url": getattr(result, "url", url) or url,
        "headers": headers,
        "cookies": cookies,
        "scripts": extract_scripts(html),
        "meta_tags": extract_meta_tags(html),
        "inline_scripts": extract_inline_scripts(html),
        "link_tags": extract_link_tags(html),
    }


async def _fetch_dns(domain: str) -> dict:
    """Query DNS records for a domain."""
    result: dict = {
        "mx_records": [],
        "txt_records": [],
        "cname_records": {},
        "ns_records": [],
    }

    resolver = dns.resolver.Resolver()
    resolver.timeout = 5
    resolver.lifetime = 10

    # MX records
    try:
        mx_answers = await asyncio.to_thread(resolver.resolve, domain, "MX")
        result["mx_records"] = [str(r.exchange).rstrip(".").lower() for r in mx_answers]
    except Exception:
        pass

    # TXT records
    try:
        txt_answers = await asyncio.to_thread(resolver.resolve, domain, "TXT")
        for rdata in txt_answers:
            for s in rdata.strings:
                result["txt_records"].append(s.decode("utf-8", errors="replace"))
    except Exception:
        pass

    # NS records
    try:
        ns_answers = await asyncio.to_thread(resolver.resolve, domain, "NS")
        result["ns_records"] = [str(r.target).rstrip(".").lower() for r in ns_answers]
    except Exception:
        pass

    # CNAME records for common subdomains
    async def _probe_cname(subdomain: str) -> tuple[str, str] | None:
        fqdn = f"{subdomain}.{domain}"
        try:
            answers = await asyncio.to_thread(resolver.resolve, fqdn, "CNAME")
            for r in answers:
                return subdomain, str(r.target).rstrip(".").lower()
        except Exception:
            return None

    cname_tasks = [_probe_cname(sub) for sub in CNAME_SUBDOMAINS]
    cname_results = await asyncio.gather(*cname_tasks, return_exceptions=True)
    for cr in cname_results:
        if isinstance(cr, tuple) and cr is not None:
            result["cname_records"][cr[0]] = cr[1]

    return result


async def _fetch_ssl(hostname: str) -> dict:
    """Inspect SSL/TLS certificate."""
    result: dict = {"ssl_issuer": "", "ssl_subject": {}, "ssl_san": []}

    def _get_cert():
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=hostname) as s:
            s.settimeout(5)
            s.connect((hostname, 443))
            return s.getpeercert()

    try:
        cert = await asyncio.to_thread(_get_cert)
        if not cert:
            return result

        # Issuer
        issuer_parts = cert.get("issuer", ())
        for part in issuer_parts:
            for key, value in part:
                if key == "organizationName":
                    result["ssl_issuer"] = value

        # Subject
        subject_parts = cert.get("subject", ())
        for part in subject_parts:
            for key, value in part:
                result["ssl_subject"][key] = value

        # SAN
        san_list = cert.get("subjectAltName", ())
        result["ssl_san"] = [value for _, value in san_list]

    except Exception as e:
        logger.debug("SSL inspection failed for %s: %s", hostname, e)

    return result


async def _fetch_supplementary(url: str) -> dict:
    """Fetch robots.txt, sitemap.xml, and favicon."""
    result: dict = {"robots_txt": None, "sitemap_xml": None, "favicon_hash": None}

    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"

    async with httpx.AsyncClient(
        timeout=10, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0 TechStackIntel/1.0"}
    ) as client:

        async def _fetch_text(path: str) -> str | None:
            try:
                resp = await client.get(f"{base}{path}")
                if resp.status_code == 200:
                    return resp.text
            except Exception:
                pass
            return None

        async def _fetch_favicon_hash() -> str | None:
            try:
                resp = await client.get(f"{base}/favicon.ico")
                if resp.status_code == 200 and len(resp.content) > 0:
                    return hashlib.md5(resp.content).hexdigest()
            except Exception:
                pass
            return None

        robots, sitemap, fav = await asyncio.gather(
            _fetch_text("/robots.txt"),
            _fetch_text("/sitemap.xml"),
            _fetch_favicon_hash(),
            return_exceptions=True,
        )

        if isinstance(robots, str):
            result["robots_txt"] = robots
        if isinstance(sitemap, str):
            result["sitemap_xml"] = sitemap
        if isinstance(fav, str):
            result["favicon_hash"] = fav

    return result


async def build_target(url: str) -> DetectionTarget:
    """Build a DetectionTarget by running all data collection in parallel."""
    url = normalize_url(url)
    domain = extract_domain(url)
    hostname = urlparse(url).hostname or domain

    # Run page fetch, DNS, SSL, and supplementary fetches in parallel
    page_task = _fetch_page(url)
    dns_task = _fetch_dns(domain)
    ssl_task = _fetch_ssl(hostname)
    supp_task = _fetch_supplementary(url)

    page_data, dns_data, ssl_data, supp_data = await asyncio.gather(
        page_task, dns_task, ssl_task, supp_task,
        return_exceptions=True,
    )

    # Start with defaults
    target = DetectionTarget(url=url, final_url=url, domain=domain)

    # Apply page data
    if isinstance(page_data, dict):
        target.html = page_data["html"]
        target.final_url = page_data["final_url"]
        target.headers = page_data["headers"]
        target.cookies = page_data["cookies"]
        target.scripts = page_data["scripts"]
        target.meta_tags = page_data["meta_tags"]
        target.inline_scripts = page_data["inline_scripts"]
        target.link_tags = page_data["link_tags"]
    elif isinstance(page_data, Exception):
        logger.error("Page fetch failed: %s", page_data)

    # Apply DNS data
    if isinstance(dns_data, dict):
        target.mx_records = dns_data["mx_records"]
        target.txt_records = dns_data["txt_records"]
        target.cname_records = dns_data["cname_records"]
        target.ns_records = dns_data["ns_records"]
    elif isinstance(dns_data, Exception):
        logger.error("DNS fetch failed: %s", dns_data)

    # Apply SSL data
    if isinstance(ssl_data, dict):
        target.ssl_issuer = ssl_data["ssl_issuer"]
        target.ssl_subject = ssl_data["ssl_subject"]
        target.ssl_san = ssl_data["ssl_san"]
    elif isinstance(ssl_data, Exception):
        logger.error("SSL fetch failed: %s", ssl_data)

    # Apply supplementary data
    if isinstance(supp_data, dict):
        target.robots_txt = supp_data["robots_txt"]
        target.sitemap_xml = supp_data["sitemap_xml"]
        target.favicon_hash = supp_data["favicon_hash"]
    elif isinstance(supp_data, Exception):
        logger.error("Supplementary fetch failed: %s", supp_data)

    return target
