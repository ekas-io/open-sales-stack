"""Unit and integration tests for the scrape_linkedin_profile tool."""

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
async def test_profile_returns_error_on_exception():
    """If the scraper raises, the tool returns a JSON error."""
    with patch("tools.profile.get_authenticated_browser", new_callable=AsyncMock) as mock_browser:
        mock_browser.side_effect = RuntimeError("auth failed")
        from tools.profile import scrape_linkedin_profile

        result = await scrape_linkedin_profile("https://linkedin.com/in/satyanadella/")
        data = json.loads(result)
        assert "error" in data
        assert data["status"] == "failed"


@pytest.mark.asyncio
async def test_profile_serializes_model_dump():
    """model_dump() is called if available."""
    mock_person = MagicMock()
    mock_person.model_dump.return_value = {"name": "Satya Nadella", "headline": "CEO at Microsoft"}

    mock_scraper = AsyncMock()
    mock_scraper.scrape.return_value = mock_person

    mock_browser_instance = AsyncMock()
    mock_browser_instance.page = MagicMock()

    with (
        patch("tools.profile.get_authenticated_browser", new_callable=AsyncMock, return_value=mock_browser_instance),
        patch("linkedin_scraper.PersonScraper", return_value=mock_scraper),
    ):
        from tools.profile import scrape_linkedin_profile

        result = await scrape_linkedin_profile("https://linkedin.com/in/satyanadella/")
        data = json.loads(result)
        assert data["name"] == "Satya Nadella"


@pytest.mark.asyncio
async def test_scrape_real_profile():
    """Scrape Satya Nadella's LinkedIn profile and verify structured data is returned.

    Requires LINKEDIN_EMAIL and LINKEDIN_PASSWORD in .env, or a saved
    linkedin_session.json from a prior manual login.
    """
    from tools.profile import scrape_linkedin_profile

    result = await scrape_linkedin_profile("https://www.linkedin.com/in/satyanadella/")
    data = json.loads(result)

    if isinstance(data, dict) and data.get("status") == "failed":
        pytest.fail(f"Profile scrape failed: {data.get('error')}")

    assert isinstance(data, dict), "Expected a dict of profile data"
    assert len(data) > 0, "Expected non-empty profile data"
