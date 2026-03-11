"""Unit and integration tests for the scrape_linkedin_company_posts tool."""

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

from tools.company_posts import _serialize


class TestSerialize:
    def test_list_of_models(self):
        item = MagicMock()
        item.model_dump.return_value = {"text": "Hello"}
        result = _serialize([item])
        assert result == [{"text": "Hello"}]

    def test_single_model(self):
        item = MagicMock()
        item.model_dump.return_value = {"text": "World"}
        result = _serialize(item)
        assert result == {"text": "World"}

    def test_plain_dict_passthrough(self):
        data = {"text": "plain"}
        assert _serialize(data) == {"text": "plain"}


@pytest.mark.asyncio
async def test_posts_returns_error_on_exception():
    """If the scraper raises, the tool returns a JSON error."""
    with patch("tools.company_posts.get_authenticated_browser", new_callable=AsyncMock) as mock_browser:
        mock_browser.side_effect = RuntimeError("auth failed")
        from tools.company_posts import scrape_linkedin_company_posts

        result = await scrape_linkedin_company_posts("https://linkedin.com/company/anthropic/")
        data = json.loads(result)
        assert "error" in data
        assert data["status"] == "failed"


@pytest.mark.asyncio
async def test_scrape_real_company_posts():
    """Scrape recent posts from Anthropic's LinkedIn company page.

    Requires LINKEDIN_EMAIL and LINKEDIN_PASSWORD in .env, or a saved
    linkedin_session.json from a prior manual login.
    """
    from tools.company_posts import scrape_linkedin_company_posts

    result = await scrape_linkedin_company_posts("https://www.linkedin.com/company/anthropic/")
    data = json.loads(result)

    # Posts come back as a list; errors come back as a dict with status=failed
    if isinstance(data, dict) and data.get("status") == "failed":
        pytest.fail(f"Company posts scrape failed: {data.get('error')}")

    assert isinstance(data, list), "Expected a list of posts"
