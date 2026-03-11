"""Unit and integration tests for the extract_job_description tool."""

import json
import os
import sys

import pytest
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Load .env so crawl4ai and any API keys are available
_pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_root_dir = os.path.dirname(os.path.dirname(_pkg_dir))
load_dotenv(os.path.join(_pkg_dir, ".env"))
load_dotenv(os.path.join(_root_dir, ".env"))

from tools.extract_job_description import _validate_extract_params


class TestValidateExtractParams:
    def test_missing_protocol(self):
        error = _validate_extract_params("jobs.lever.co/anthropic", "single")
        assert error is not None
        assert "protocol" in json.loads(error)["error"]

    def test_invalid_mode(self):
        error = _validate_extract_params("https://jobs.lever.co/anthropic", "bad_mode")
        assert error is not None
        assert "mode" in json.loads(error)["error"]

    def test_linkedin_url_blocked(self):
        error = _validate_extract_params("https://www.linkedin.com/jobs/view/123", "single")
        assert error is not None
        assert "LinkedIn" in json.loads(error)["error"]

    def test_valid_single(self):
        error = _validate_extract_params("https://jobs.lever.co/anthropic", "single")
        assert error is None

    def test_valid_crawl(self):
        error = _validate_extract_params("https://boards.greenhouse.io/anthropic", "crawl")
        assert error is None


@pytest.mark.asyncio
async def test_extract_returns_error_for_bad_url():
    from tools.extract_job_description import extract_job_description

    result = await extract_job_description("not-a-url", "single")
    data = json.loads(result)
    assert "error" in data


@pytest.mark.asyncio
async def test_extract_blocks_linkedin():
    from tools.extract_job_description import extract_job_description

    result = await extract_job_description("https://linkedin.com/jobs/view/123", "single")
    data = json.loads(result)
    assert "error" in data
    assert "LinkedIn" in data["error"]


@pytest.mark.asyncio
async def test_extract_single_real_page():
    """Fetch Anthropic's Lever jobs listing as a single page and verify markdown content."""
    from tools.extract_job_description import extract_job_description

    result = await extract_job_description("https://jobs.lever.co/anthropic", "single")
    data = json.loads(result)
    assert data.get("status") == "completed", f"Single page fetch failed: {data}"
    assert data.get("url") == "https://jobs.lever.co/anthropic"
    assert data.get("markdown"), "Expected non-empty markdown content"


@pytest.mark.asyncio
async def test_extract_crawl_real_careers():
    """Crawl Anthropic's Greenhouse job board and verify pages are returned."""
    from tools.extract_job_description import extract_job_description

    result = await extract_job_description(
        "https://boards.greenhouse.io/anthropic", "crawl", max_pages=1
    )
    data = json.loads(result)
    assert data.get("status") == "completed", f"Crawl failed: {data}"
    assert "pages_found" in data
    assert data["pages_found"] >= 1, "Expected at least one page crawled"
    assert data["careers_url"] == "https://boards.greenhouse.io/anthropic"
