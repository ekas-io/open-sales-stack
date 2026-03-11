"""Unit and integration tests for the scrape_linkedin_company tool."""

import json
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Load .env so LINKEDIN_EMAIL / LINKEDIN_PASSWORD are available
_pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_root_dir = os.path.dirname(os.path.dirname(_pkg_dir))
load_dotenv(os.path.join(_pkg_dir, ".env"))
load_dotenv(os.path.join(_root_dir, ".env"))


@pytest.mark.asyncio
async def test_company_returns_error_on_exception():
    """If the scraper raises, the tool returns a JSON error."""
    with patch("tools.company.get_authenticated_browser", new_callable=AsyncMock) as mock_browser:
        mock_browser.side_effect = RuntimeError("auth failed")
        from tools.company import scrape_linkedin_company

        result = await scrape_linkedin_company("https://linkedin.com/company/microsoft/")
        data = json.loads(result)
        assert "error" in data
        assert data["status"] == "failed"


@pytest.mark.asyncio
async def test_company_serializes_model_dump():
    """model_dump() is called if available on the returned object."""
    mock_company = MagicMock()
    mock_company.model_dump.return_value = {"name": "Microsoft", "industry": "Technology"}

    mock_scraper = AsyncMock()
    mock_scraper.scrape.return_value = mock_company

    mock_browser_instance = AsyncMock()
    mock_browser_instance.page = MagicMock()

    with (
        patch("tools.company.get_authenticated_browser", new_callable=AsyncMock, return_value=mock_browser_instance),
        patch("linkedin_scraper.CompanyScraper", return_value=mock_scraper),
    ):
        from tools.company import scrape_linkedin_company

        result = await scrape_linkedin_company("https://linkedin.com/company/microsoft/")
        data = json.loads(result)
        assert data["name"] == "Microsoft"


@pytest.mark.asyncio
async def test_scrape_real_company():
    """Scrape Microsoft's LinkedIn company page and verify structured data is returned.

    Requires LINKEDIN_EMAIL and LINKEDIN_PASSWORD in .env, or a saved
    linkedin_session.json from a prior manual login.
    """
    from tools.company import scrape_linkedin_company

    result = await scrape_linkedin_company("https://www.linkedin.com/company/microsoft/")
    data = json.loads(result)

    if isinstance(data, dict) and data.get("status") == "failed":
        pytest.fail(f"Company scrape failed: {data.get('error')}")

    assert isinstance(data, dict), "Expected a dict of company data"
    assert len(data) > 0, "Expected non-empty company data"
