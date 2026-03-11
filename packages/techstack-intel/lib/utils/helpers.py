"""Utility helpers for domain extraction, URL normalization, and hashing."""

from __future__ import annotations

import hashlib
import re
from urllib.parse import urlparse

import tldextract


def extract_domain(url: str) -> str:
    """Extract the registered domain from a URL (e.g. 'www.example.com' -> 'example.com')."""
    ext = tldextract.extract(url)
    if ext.suffix:
        return f"{ext.domain}.{ext.suffix}"
    return ext.domain


def normalize_url(url: str) -> str:
    """Ensure URL has a scheme."""
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    return url


def md5_hash(data: bytes) -> str:
    """Return hex MD5 hash of bytes."""
    return hashlib.md5(data).hexdigest()


def mmh3_hash_favicon(data: bytes) -> str:
    """Return MMH3 hash of base64-encoded favicon data (Shodan-style).

    Falls back to MD5 if mmh3 is not installed.
    """
    import base64

    b64 = base64.encodebytes(data)
    try:
        import mmh3

        return str(mmh3.hash(b64))
    except ImportError:
        return md5_hash(data)


def extract_scripts(html: str) -> list[str]:
    """Extract all <script src="..."> URLs from HTML."""
    return re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html, re.IGNORECASE)


def extract_inline_scripts(html: str) -> list[str]:
    """Extract contents of inline <script> blocks."""
    return re.findall(
        r"<script(?:\s[^>]*)?>(.+?)</script>", html, re.IGNORECASE | re.DOTALL
    )


def extract_meta_tags(html: str) -> dict[str, str]:
    """Extract <meta name="..." content="..."> pairs."""
    tags: dict[str, str] = {}
    for match in re.finditer(
        r'<meta\s+(?:[^>]*?\s)?name=["\']([^"\']+)["\'][^>]*?\scontent=["\']([^"\']*)["\']',
        html,
        re.IGNORECASE,
    ):
        tags[match.group(1).lower()] = match.group(2)
    # Also match content before name
    for match in re.finditer(
        r'<meta\s+(?:[^>]*?\s)?content=["\']([^"\']*)["\'][^>]*?\sname=["\']([^"\']+)["\']',
        html,
        re.IGNORECASE,
    ):
        tags[match.group(2).lower()] = match.group(1)
    return tags


def extract_link_tags(html: str) -> list[str]:
    """Extract all <link href="..."> values."""
    return re.findall(r'<link[^>]+href=["\']([^"\']+)["\']', html, re.IGNORECASE)


def extract_version_from_url(url: str, prefix: str) -> str | None:
    """Try to extract a version number from a script URL.

    e.g. 'jquery-3.6.0.min.js' -> '3.6.0'
    """
    match = re.search(rf"{re.escape(prefix)}[/-]?v?(\d+(?:\.\d+)+)", url, re.IGNORECASE)
    if match:
        return match.group(1)
    return None


def get_hostname(url: str) -> str:
    """Get hostname from URL."""
    parsed = urlparse(url)
    return parsed.hostname or ""
