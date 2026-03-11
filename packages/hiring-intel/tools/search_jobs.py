"""Job search tool for hiring-intel."""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger("hiring-intel")

VALID_SITES = ["linkedin", "indeed", "glassdoor", "google", "zip_recruiter", "bayt"]
VALID_JOB_TYPES = ["fulltime", "parttime", "internship", "contract"]

JOBSPY_PROXIES = os.environ.get("JOBSPY_PROXIES", "")
JOBSPY_CA_CERT = os.environ.get("JOBSPY_CA_CERT", "")


def _parse_proxy_list() -> list[str] | None:
    """Parse JOBSPY_PROXIES env var into a list."""
    if not JOBSPY_PROXIES:
        return None
    proxies = [p.strip() for p in JOBSPY_PROXIES.split(",") if p.strip()]
    return proxies if proxies else None


def _build_jobspy_kwargs(
    search_term, site_name, location, distance, job_type, is_remote,
    results_wanted, hours_old, country_indeed, linkedin_fetch_description,
    linkedin_company_ids, google_search_term, easy_apply,
    enforce_annual_salary, offset, description_format,
) -> dict:
    """Build the kwargs dict for a jobspy scrape_jobs call."""
    kwargs: dict = {
        "search_term": search_term,
        "results_wanted": results_wanted,
        "description_format": description_format,
        "enforce_annual_salary": enforce_annual_salary,
        "verbose": 0,
        "site_name": site_name or ["indeed", "linkedin", "glassdoor", "google", "zip_recruiter"],
    }
    for key, val in {
        "location": location, "distance": distance, "job_type": job_type,
        "is_remote": is_remote, "hours_old": hours_old,
        "country_indeed": country_indeed, "easy_apply": easy_apply, "offset": offset,
    }.items():
        if val is not None:
            kwargs[key] = val

    if linkedin_fetch_description:
        kwargs["linkedin_fetch_description"] = True
    if linkedin_company_ids:
        kwargs["linkedin_company_ids"] = linkedin_company_ids
    if google_search_term:
        kwargs["google_search_term"] = google_search_term

    proxies = _parse_proxy_list()
    if proxies:
        kwargs["proxies"] = proxies
    if JOBSPY_CA_CERT:
        kwargs["ca_cert"] = JOBSPY_CA_CERT

    return kwargs


def _clean_records(df) -> list[dict]:
    """Convert a jobspy DataFrame to a list of clean, JSON-serializable dicts."""
    if df.empty:
        return []
    records = df.where(df.notnull(), None).to_dict(orient="records")
    cleaned = []
    for record in records:
        clean = {}
        for k, v in record.items():
            if v is None:
                continue
            if hasattr(v, "isoformat"):
                clean[k] = v.isoformat()
            elif isinstance(v, (int, float, str, bool)):
                clean[k] = v
            else:
                clean[k] = str(v)
        cleaned.append(clean)
    return cleaned


def _run_jobspy(kwargs: dict) -> list[dict]:
    """Run jobspy scrape_jobs synchronously and return clean records."""
    from jobspy import scrape_jobs

    df = scrape_jobs(**kwargs)
    return _clean_records(df)


def _validate_params(site_name, job_type, description_format, results_wanted):
    """Validate search parameters. Returns (error_json | None, (fmt, count))."""
    if site_name:
        invalid = [s for s in site_name if s not in VALID_SITES]
        if invalid:
            return json.dumps({"error": f"Invalid site(s): {invalid}. Valid: {VALID_SITES}"}), None
    if job_type and job_type not in VALID_JOB_TYPES:
        return json.dumps({"error": f"Invalid job_type: {job_type}. Valid: {VALID_JOB_TYPES}"}), None
    if description_format not in ("markdown", "html"):
        description_format = "markdown"
    return None, (description_format, min(results_wanted, 50))


async def search_jobs(
    search_term, site_name, location, distance, job_type, is_remote,
    results_wanted, hours_old, country_indeed, linkedin_fetch_description,
    linkedin_company_ids, google_search_term, easy_apply,
    enforce_annual_salary, offset, description_format,
) -> str:
    """Search for job postings and return a JSON string."""
    error, cleaned = _validate_params(site_name, job_type, description_format, results_wanted)
    if error:
        return error
    description_format, results_wanted = cleaned

    kwargs = _build_jobspy_kwargs(
        search_term, site_name, location, distance, job_type, is_remote,
        results_wanted, hours_old, country_indeed, linkedin_fetch_description,
        linkedin_company_ids, google_search_term, easy_apply,
        enforce_annual_salary, offset, description_format,
    )

    try:
        results = await asyncio.to_thread(_run_jobspy, kwargs)
        return json.dumps({
            "jobs": results,
            "total": len(results),
            "search_term": search_term,
            "status": "completed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }, default=str)
    except Exception as e:
        logger.error("Job search failed: %s", e)
        return json.dumps({"error": str(e), "status": "failed"})
