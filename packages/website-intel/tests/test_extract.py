"""Unit and integration tests for the website_intel_extract tool."""

import json
import os
import sys

import pytest
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Load .env from package dir and repo root so LLM_API_KEY / LLM_PROVIDER are set
_pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_root_dir = os.path.dirname(os.path.dirname(_pkg_dir))
load_dotenv(os.path.join(_pkg_dir, ".env"))
load_dotenv(os.path.join(_root_dir, ".env"))

from tools.extract import _validate_params


class TestValidateParams:
    def test_missing_protocol(self):
        error, _ = _validate_params("ekas.io", "scrape", 5)
        assert error is not None
        assert "protocol" in json.loads(error)["error"]

    def test_invalid_mode(self):
        error, _ = _validate_params("https://ekas.io", "stream", 5)
        assert error is not None
        assert "mode" in json.loads(error)["error"]

    def test_limit_clamped_high(self):
        _, limit = _validate_params("https://ekas.io", "scrape", 100)
        assert limit == 10

    def test_limit_clamped_low(self):
        _, limit = _validate_params("https://ekas.io", "scrape", 0)
        assert limit == 1

    def test_valid_scrape(self):
        error, limit = _validate_params("https://ekas.io", "scrape", 5)
        assert error is None
        assert limit == 5

    def test_valid_crawl(self):
        error, limit = _validate_params("https://ekas.io", "crawl", 3)
        assert error is None
        assert limit == 3


@pytest.mark.asyncio
async def test_extract_returns_error_for_bad_url():
    from tools.extract import website_intel_extract

    result = await website_intel_extract("not-a-url", {}, "extract data")
    data = json.loads(result)
    assert "error" in data


@pytest.mark.asyncio
async def test_extract_returns_error_for_bad_mode():
    from tools.extract import website_intel_extract

    result = await website_intel_extract("https://ekas.io", {}, "extract data", mode="stream")
    data = json.loads(result)
    assert "error" in data


@pytest.mark.asyncio
async def test_extract_real_scrape():
    """Scrape ekas.io and verify structured content is returned.

    Requires LLM_API_KEY and LLM_PROVIDER set in .env (repo root or package).
    """
    from tools.extract import website_intel_extract

    result = await website_intel_extract(
        "https://ekas.io",
        {},
        "Extract the page title and main heading",
        mode="scrape",
    )
    data = json.loads(result)
    assert data.get("status") == "completed", f"Extraction failed: {data}"
    assert "data" in data
    assert "timestamp" in data
