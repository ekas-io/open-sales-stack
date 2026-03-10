# Ad Intel MCP Server

Competitive ad intelligence from Meta Ad Library and LinkedIn Ad Library.

Part of the [Open Sales Stack](../../README.md) monorepo.

## Tools

### `ad_intel_meta_search`

Search the Meta Ad Library for active ads by keyword, advertiser, or topic.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | str | Yes | — | Search keyword or advertiser name |
| `country` | str | No | `"US"` | 2-letter country code |
| `ad_type` | str | No | `"all"` | `all`, `political_and_issue_ads`, `housing_ads`, `employment_ads`, `credit_ads` |
| `start_date_min` | str | No | — | YYYY-MM-DD start date filter |
| `start_date_max` | str | No | — | YYYY-MM-DD end date filter |

### `ad_intel_linkedin_search`

Search the LinkedIn Ad Library for ads by account owner, payer, or keyword.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `account_owner` | str | One of three* | — | Company handle (e.g. "notion") |
| `payer` | str | One of three* | — | Payer name |
| `keyword` | str | One of three* | — | Keyword search |
| `countries` | str | No | — | Comma-separated 2-letter codes |
| `date_option` | str | No | — | `last-30-days`, `current-month`, `current-year`, `last-year`, `custom-date-range` |
| `start_date` | str | Conditional | — | Required if `date_option` is `custom-date-range` |
| `end_date` | str | Conditional | — | Required if `date_option` is `custom-date-range` |
| `impressions_min_value` | int | No | — | Min impressions (in thousands) |
| `impressions_max_value` | int | No | — | Max impressions (in thousands) |

*At least one of `account_owner`, `payer`, or `keyword` must be provided.

## Prerequisites

- Running crawl4ai instance (default: `http://localhost:11235`)
- OpenAI API key for LLM extraction

```bash
# Start crawl4ai
docker run -p 11235:11235 unclecode/crawl4ai
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CRAWL4AI_BASE_URL` | `http://localhost:11235` | crawl4ai service URL |
| `LLM_PROVIDER` | `openai/gpt-4o-mini` | LLM provider for extraction |
| `OPENAI_API_KEY` | — | Required for LLM extraction |

## Running

```bash
# Direct
python packages/ad-intel/server.py

# Via Claude Code
claude mcp add oss-ad-intel -- python packages/ad-intel/server.py
```

## Testing

```bash
# Ensure crawl4ai is running first
pytest packages/ad-intel/tests/ -v -s

# Meta tests only
pytest packages/ad-intel/tests/test_meta_ads.py -v -s

# LinkedIn tests only
pytest packages/ad-intel/tests/test_linkedin_ads.py -v -s
```

## Known Limitations

- **Meta Ad Library** is a heavy JS-rendered SPA. The crawler uses generous timeouts and anti-detection (`magic: true`) but may occasionally return partial results.
- **LinkedIn Ad Library** may return limited or no results without authentication. The tool handles this gracefully and provides a direct URL as fallback.
- Both tools are read-only and idempotent. They do not modify any state.
