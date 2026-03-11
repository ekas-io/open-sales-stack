"""Unit tests for individual detectors using mock DetectionTarget data."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.models import DetectionTarget
from lib.detectors.header_detector import HeaderDetector
from lib.detectors.html_detector import HTMLDetector
from lib.detectors.dns_detector import DNSDetector
from lib.detectors.ssl_detector import SSLDetector
from lib.detectors.robots_detector import RobotsDetector
from lib.detectors.cookie_detector import CookieDetector
from lib.detectors.favicon_detector import FaviconDetector


def _make_target(**kwargs) -> DetectionTarget:
    defaults = {"url": "https://test.com", "final_url": "https://test.com", "domain": "test.com"}
    defaults.update(kwargs)
    return DetectionTarget(**defaults)


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class TestHeaderDetector:
    def test_nginx_server(self):
        target = _make_target(headers={"server": "nginx/1.21.0"})
        results = run(HeaderDetector().detect(target))
        names = [r.name for r in results]
        assert "Nginx" in names
        nginx = [r for r in results if r.name == "Nginx"][0]
        assert nginx.version == "1.21.0"

    def test_cloudflare_headers(self):
        target = _make_target(headers={"cf-ray": "abc123", "server": "cloudflare"})
        results = run(HeaderDetector().detect(target))
        names = [r.name for r in results]
        assert "Cloudflare" in names

    def test_vercel_headers(self):
        target = _make_target(headers={"x-vercel-id": "iad1::abc"})
        results = run(HeaderDetector().detect(target))
        names = [r.name for r in results]
        assert "Vercel" in names

    def test_powered_by_nextjs(self):
        target = _make_target(headers={"x-powered-by": "Next.js"})
        results = run(HeaderDetector().detect(target))
        names = [r.name for r in results]
        assert "Next.js" in names

    def test_empty_headers(self):
        target = _make_target(headers={})
        results = run(HeaderDetector().detect(target))
        assert results == []


class TestHTMLDetector:
    def test_wordpress_detection(self):
        target = _make_target(
            html='<link rel="stylesheet" href="/wp-content/themes/my-theme/style.css">',
            scripts=[], inline_scripts=[], link_tags=["/wp-content/themes/my-theme/style.css"],
        )
        results = run(HTMLDetector().detect(target))
        names = [r.name for r in results]
        assert "WordPress" in names

    def test_nextjs_detection(self):
        target = _make_target(
            html='<script id="__NEXT_DATA__" type="application/json">{"buildId":"abc"}</script>',
            scripts=["/_next/static/chunks/main.js"],
            inline_scripts=['{"buildId":"abc"}'],
            link_tags=[],
        )
        results = run(HTMLDetector().detect(target))
        names = [r.name for r in results]
        assert "Next.js" in names

    def test_react_detection(self):
        target = _make_target(
            html='<div data-reactroot="">',
            scripts=[], inline_scripts=[], link_tags=[],
        )
        results = run(HTMLDetector().detect(target))
        names = [r.name for r in results]
        assert "React" in names

    def test_google_analytics(self):
        target = _make_target(
            html='<script src="https://www.googletagmanager.com/gtag/js?id=G-ABC"></script>',
            scripts=["https://www.googletagmanager.com/gtag/js?id=G-ABC"],
            inline_scripts=[], link_tags=[],
        )
        results = run(HTMLDetector().detect(target))
        names = [r.name for r in results]
        assert "Google Analytics" in names

    def test_hubspot_marketing(self):
        target = _make_target(
            html='<script src="https://js.hs-scripts.com/12345.js"></script>',
            scripts=["https://js.hs-scripts.com/12345.js"],
            inline_scripts=[], link_tags=[],
        )
        results = run(HTMLDetector().detect(target))
        names = [r.name for r in results]
        assert "HubSpot" in names

    def test_stripe_detection(self):
        target = _make_target(
            html='<script src="https://js.stripe.com/v3/"></script>',
            scripts=["https://js.stripe.com/v3/"],
            inline_scripts=[], link_tags=[],
        )
        results = run(HTMLDetector().detect(target))
        names = [r.name for r in results]
        assert "Stripe" in names

    def test_meta_generator(self):
        target = _make_target(
            html='<meta name="generator" content="WordPress 6.4.2">',
            meta_tags={"generator": "WordPress 6.4.2"},
            scripts=[], inline_scripts=[], link_tags=[],
        )
        results = run(HTMLDetector().detect(target))
        wp_results = [r for r in results if r.name == "WordPress"]
        assert len(wp_results) > 0
        assert wp_results[0].version == "6.4.2"


class TestDNSDetector:
    def test_google_workspace_mx(self):
        target = _make_target(mx_records=["aspmx.l.google.com", "alt1.aspmx.l.google.com"])
        results = run(DNSDetector().detect(target))
        names = [r.name for r in results]
        assert "Google Workspace" in names

    def test_microsoft_365_spf(self):
        target = _make_target(txt_records=["v=spf1 include:spf.protection.outlook.com ~all"])
        results = run(DNSDetector().detect(target))
        names = [r.name for r in results]
        assert "Microsoft 365" in names

    def test_cloudflare_ns(self):
        target = _make_target(ns_records=["ns1.cloudflare.com", "ns2.cloudflare.com"])
        results = run(DNSDetector().detect(target))
        names = [r.name for r in results]
        assert "Cloudflare DNS" in names

    def test_github_pages_cname(self):
        target = _make_target(cname_records={"www": "mysite.github.io"})
        results = run(DNSDetector().detect(target))
        names = [r.name for r in results]
        assert "GitHub Pages" in names

    def test_verification_records(self):
        target = _make_target(txt_records=["google-site-verification=abc123"])
        results = run(DNSDetector().detect(target))
        names = [r.name for r in results]
        assert "Google Search Console" in names


class TestSSLDetector:
    def test_lets_encrypt(self):
        target = _make_target(ssl_issuer="Let's Encrypt")
        results = run(SSLDetector().detect(target))
        names = [r.name for r in results]
        assert "Let's Encrypt" in names

    def test_cloudflare_ssl(self):
        target = _make_target(ssl_issuer="Cloudflare, Inc.")
        results = run(SSLDetector().detect(target))
        names = [r.name for r in results]
        assert "Cloudflare" in names


class TestRobotsDetector:
    def test_wordpress_robots(self):
        target = _make_target(robots_txt="Disallow: /wp-admin/\nAllow: /wp-admin/admin-ajax.php")
        results = run(RobotsDetector().detect(target))
        names = [r.name for r in results]
        assert "WordPress" in names

    def test_yoast_sitemap(self):
        target = _make_target(sitemap_xml='<?xml version="1.0"?><!-- Yoast SEO plugin -->')
        results = run(RobotsDetector().detect(target))
        names = [r.name for r in results]
        assert "Yoast SEO" in names


class TestCookieDetector:
    def test_google_analytics_cookie(self):
        target = _make_target(cookies=[{"name": "_ga", "value": "GA1.2.123"}])
        results = run(CookieDetector().detect(target))
        names = [r.name for r in results]
        assert "Google Analytics" in names

    def test_hubspot_cookies(self):
        target = _make_target(cookies=[
            {"name": "__hstc", "value": "abc"},
            {"name": "hubspotutk", "value": "def"},
        ])
        results = run(CookieDetector().detect(target))
        names = [r.name for r in results]
        assert "HubSpot" in names

    def test_shopify_cookie_prefix(self):
        target = _make_target(cookies=[{"name": "_shopify_s", "value": "abc"}])
        results = run(CookieDetector().detect(target))
        names = [r.name for r in results]
        assert "Shopify" in names


class TestFaviconDetector:
    def test_known_hash(self):
        target = _make_target(favicon_hash="b25e29432b278e3e33919be498c76a2c")
        results = run(FaviconDetector().detect(target))
        names = [r.name for r in results]
        assert "WordPress" in names

    def test_unknown_hash(self):
        target = _make_target(favicon_hash="0000000000000000000000000000dead")
        results = run(FaviconDetector().detect(target))
        assert results == []


def run_all_tests():
    """Run all tests and report results."""
    test_classes = [
        TestHeaderDetector,
        TestHTMLDetector,
        TestDNSDetector,
        TestSSLDetector,
        TestRobotsDetector,
        TestCookieDetector,
        TestFaviconDetector,
    ]

    total = 0
    passed = 0
    failed = 0
    errors = []

    for cls in test_classes:
        instance = cls()
        methods = [m for m in dir(instance) if m.startswith("test_")]
        for method_name in methods:
            total += 1
            try:
                getattr(instance, method_name)()
                passed += 1
                print(f"  PASS: {cls.__name__}.{method_name}")
            except Exception as e:
                failed += 1
                errors.append((f"{cls.__name__}.{method_name}", str(e)))
                print(f"  FAIL: {cls.__name__}.{method_name}: {e}")

    print(f"\n{'='*60}")
    print(f"Results: {passed}/{total} passed, {failed} failed")
    if errors:
        print("\nFailures:")
        for name, err in errors:
            print(f"  - {name}: {err}")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
