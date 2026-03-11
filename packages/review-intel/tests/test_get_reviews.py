"""Unit tests for the get_reviews tool (stub)."""

import json
import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.mark.asyncio
async def test_get_reviews_returns_not_implemented():
    from tools.get_reviews import get_reviews

    result = await get_reviews("Salesforce", "g2")
    data = json.loads(result)
    assert "error" in data
    assert "not yet implemented" in data["error"]


@pytest.mark.asyncio
async def test_get_reviews_default_platform():
    from tools.get_reviews import get_reviews

    result = await get_reviews("Salesforce")
    data = json.loads(result)
    assert "error" in data
