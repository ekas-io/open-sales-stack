"""
URL construction helpers for Meta and LinkedIn Ad Libraries.
"""

from urllib.parse import urlencode


def build_meta_ad_library_url(
    query: str,
    country: str = "US",
    ad_type: str = "all",
    start_date_min: str | None = None,
    start_date_max: str | None = None,
) -> str:
    """
    Build a Meta Ad Library search URL.

    Args:
        query: Search keyword or advertiser name.
        country: 2-letter country code.
        ad_type: One of: all, political_and_issue_ads, housing_ads,
                 employment_ads, credit_ads.
        start_date_min: Optional YYYY-MM-DD start date filter.
        start_date_max: Optional YYYY-MM-DD end date filter.

    Returns:
        Fully constructed Meta Ad Library URL.
    """
    params: dict[str, str] = {
        "active_status": "active",
        "ad_type": ad_type,
        "country": country,
        "is_targeted_country": "false",
        "media_type": "all",
        "q": query,
        "search_type": "keyword_unordered",
        "sort_data[direction]": "desc",
        "sort_data[mode]": "total_impressions",
    }

    # Only include date params if explicitly provided
    if start_date_min is not None:
        params["start_date[min]"] = start_date_min
    if start_date_max is not None:
        params["start_date[max]"] = start_date_max

    return f"https://www.facebook.com/ads/library/?{urlencode(params)}"


def build_linkedin_ad_library_url(
    account_owner: str | None = None,
    payer: str | None = None,
    keyword: str | None = None,
    countries: str | None = None,
    date_option: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    impressions_min_value: int | None = None,
    impressions_max_value: int | None = None,
) -> str:
    """
    Build a LinkedIn Ad Library search URL.

    Args:
        account_owner: Company name/handle.
        payer: Payer name.
        keyword: Keyword search.
        countries: Comma-separated 2-letter country codes.
        date_option: One of: last-30-days, current-month, current-year,
                     last-year, custom-date-range.
        start_date: YYYY-MM-DD, required if date_option is custom-date-range.
        end_date: YYYY-MM-DD, required if date_option is custom-date-range.
        impressions_min_value: Min impressions (in thousands).
        impressions_max_value: Max impressions (in thousands).

    Returns:
        Fully constructed LinkedIn Ad Library URL.

    Raises:
        ValueError: If no search criteria provided or custom date range
                    is missing start/end dates.
    """
    if not any([account_owner, payer, keyword]):
        raise ValueError(
            "At least one of account_owner, payer, or keyword must be provided."
        )

    if date_option == "custom-date-range":
        if not start_date or not end_date:
            raise ValueError(
                "start_date and end_date are required when "
                "date_option is 'custom-date-range'."
            )

    params: dict[str, str] = {}

    if account_owner is not None:
        params["accountOwner"] = account_owner
    if payer is not None:
        params["payer"] = payer
    if keyword is not None:
        params["keyword"] = keyword
    if countries is not None:
        params["countries"] = countries
    if date_option is not None:
        params["dateOption"] = date_option
    if start_date is not None:
        params["startdate"] = start_date
    if end_date is not None:
        params["enddate"] = end_date
    if impressions_min_value is not None:
        params["impressionsMinValue"] = str(impressions_min_value)
        params["impressionsMinUnit"] = "thousand"
    if impressions_max_value is not None:
        params["impressionsMaxValue"] = str(impressions_max_value)
        params["impressionsMaxUnit"] = "thousand"

    return f"https://www.linkedin.com/ad-library/search?{urlencode(params)}"
