"""Unit and integration tests for the search_jobs tool."""

import json
import os
import sys

import pytest
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Load .env so any env vars (proxies, certs) are available
_pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_root_dir = os.path.dirname(os.path.dirname(_pkg_dir))
load_dotenv(os.path.join(_pkg_dir, ".env"))
load_dotenv(os.path.join(_root_dir, ".env"))

from tools.search_jobs import (
    VALID_SITES,
    VALID_JOB_TYPES,
    _parse_proxy_list,
    _clean_records,
    _validate_params,
    _build_jobspy_kwargs,
)


class TestParseProxyList:
    def test_empty_string_returns_none(self, monkeypatch):
        monkeypatch.setenv("JOBSPY_PROXIES", "")
        import tools.search_jobs as m
        m.JOBSPY_PROXIES = ""
        assert m._parse_proxy_list() is None

    def test_single_proxy(self, monkeypatch):
        import tools.search_jobs as m
        m.JOBSPY_PROXIES = "host:8080"
        result = m._parse_proxy_list()
        assert result == ["host:8080"]

    def test_multiple_proxies(self, monkeypatch):
        import tools.search_jobs as m
        m.JOBSPY_PROXIES = "host1:8080, host2:8080"
        result = m._parse_proxy_list()
        assert result == ["host1:8080", "host2:8080"]


class TestCleanRecords:
    def test_empty_dataframe(self):
        import pandas as pd
        df = pd.DataFrame()
        assert _clean_records(df) == []

    def test_isoformat_values_converted(self):
        import pandas as pd
        from datetime import date
        df = pd.DataFrame([{"title": "Engineer", "date_posted": date(2025, 1, 1)}])
        records = _clean_records(df)
        assert records[0]["date_posted"] == "2025-01-01"

    def test_none_values_dropped(self):
        import pandas as pd
        df = pd.DataFrame([{"title": "Engineer", "salary": None}])
        records = _clean_records(df)
        assert "salary" not in records[0]


class TestValidateParams:
    def test_invalid_site(self):
        error, _ = _validate_params(["badsite"], None, "markdown", 10)
        assert error is not None
        data = json.loads(error)
        assert "error" in data

    def test_invalid_job_type(self):
        error, _ = _validate_params(None, "badtype", "markdown", 10)
        assert error is not None

    def test_results_capped_at_50(self):
        error, cleaned = _validate_params(None, None, "markdown", 200)
        assert error is None
        _, count = cleaned
        assert count == 50

    def test_invalid_description_format_corrected(self):
        error, cleaned = _validate_params(None, None, "xml", 10)
        assert error is None
        fmt, _ = cleaned
        assert fmt == "markdown"

    def test_valid_params(self):
        error, cleaned = _validate_params(["indeed"], "fulltime", "html", 15)
        assert error is None
        fmt, count = cleaned
        assert fmt == "html"
        assert count == 15


class TestBuildJobspyKwargs:
    def test_defaults(self):
        kwargs = _build_jobspy_kwargs(
            "engineer", None, None, None, None, None,
            10, None, None, False, None, None, None, False, None, "markdown",
        )
        assert kwargs["search_term"] == "engineer"
        assert "indeed" in kwargs["site_name"]
        assert kwargs["results_wanted"] == 10

    def test_optional_fields_included(self):
        kwargs = _build_jobspy_kwargs(
            "engineer", ["indeed"], "NYC", 25, "fulltime", True,
            10, 48, "US", True, [123], "engineer NYC", False, False, 0, "markdown",
        )
        assert kwargs["location"] == "NYC"
        assert kwargs["distance"] == 25
        assert kwargs["linkedin_fetch_description"] is True
        assert kwargs["linkedin_company_ids"] == [123]


@pytest.mark.asyncio
async def test_search_real_jobs():
    """Search for Python developer jobs on Indeed and verify results are returned."""
    from tools.search_jobs import search_jobs

    result = await search_jobs(
        search_term="python developer",
        site_name=["indeed"],
        location="San Francisco, CA",
        distance=None,
        job_type=None,
        is_remote=None,
        results_wanted=5,
        hours_old=None,
        country_indeed=None,
        linkedin_fetch_description=None,
        linkedin_company_ids=None,
        google_search_term=None,
        easy_apply=None,
        enforce_annual_salary=False,
        offset=None,
        description_format="markdown",
    )
    data = json.loads(result)
    assert data.get("status") == "completed", f"Job search failed: {data}"
    assert "jobs" in data
    assert isinstance(data["jobs"], list)
    assert data["search_term"] == "python developer"
