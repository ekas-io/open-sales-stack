# Claude Code Prompt: Ekas Experiments Data Pipeline

## What You're Building

A Python pipeline that processes B2B SaaS company accounts to collect firmographic data (Coresignal), website intelligence, hiring signals, and ad intelligence for research experiments. The pipeline must be fault-tolerant (resume from where it left off), retry transient failures up to 5 times, and produce detailed per-account logs.

## Project Location

Create the project at: `~/projects/tiro/ekas-experiments-pipeline/`

## Architecture

```
ekas-experiments-pipeline/
├── pipeline.py              # Main entry point + CLI
├── config.py                # Rate limits, paths, env vars, retry config
├── processors/
│   ├── coresignal.py        # Coresignal company enrich API
│   ├── website.py           # Website intel (pricing, forms, CTAs, chatbot, GTM)
│   └── ads.py               # LinkedIn + Meta ad intel
├── compiler.py              # Compiles raw JSONs → master CSV + supplementary CSVs
├── requirements.txt
├── .env.example
├── data/
│   └── {domain}/            # One directory per company
│       ├── coresignal.json  # Full raw Coresignal response (dumped as-is)
│       ├── website.json     # All website-intel results
│       ├── ads.json         # LinkedIn + Meta ad results
│       └── account.log      # Per-account log file
├── output/
│   ├── master.csv           # Main output: one row per company, all flattened columns
│   ├── employee_trends.csv  # Long format: domain, date, dept, count (from Coresignal by_month)
│   ├── funding_events.csv   # Long format: domain, date, round_name, amount, currency, investors
│   ├── technologies.csv     # Long format: domain, technology, first_verified, last_verified
│   ├── keywords.csv         # Long format: domain, keyword
│   ├── job_postings.csv     # Long format: domain, title, url, location, posted_date
│   └── processing_log.csv   # domain, status, steps_succeeded, steps_failed, error_summary
└── requirements.txt
```

**Key design: one directory per company.** Each company gets `data/{domain}/` containing separate JSON files for each data source. This keeps the raw data organized and makes it easy to inspect/debug individual companies.

---

## Existing Crawler Code to Reuse

The crawlers already exist at `/Users/shuvrajit/projects/tiro/open-sales-stack/packages/`. Import and call them directly as async Python functions. **Do NOT rewrite these crawlers.**

### Website-Intel

**Location**: `/Users/shuvrajit/projects/tiro/open-sales-stack/packages/website-intel/`

**Import**:
```python
import sys
sys.path.insert(0, '/Users/shuvrajit/projects/tiro/open-sales-stack/packages/website-intel')
from tools.extract import website_intel_extract
```

**Function Signature**:
```python
async def website_intel_extract(
    url: str,
    schema: dict,       # JSON Schema defining what to extract
    prompt: str,         # Natural language instruction for what to extract
    mode: str = "scrape", # "scrape" (single page) or "crawl" (multi-page)
    limit: int = 5,      # Max pages for crawl mode (clamped 1-10)
) -> str  # Returns JSON string — always json.loads() the result
```

- Uses `crawl4ai` with `LLMExtractionStrategy` under the hood
- Requires env vars: `LLM_API_KEY`, `LLM_PROVIDER` (default: `"openai/gpt-5-mini-2025-08-07"`)
- Page timeout: 60s
- All calls are async

### Ad-Intel

**Location**: `/Users/shuvrajit/projects/tiro/open-sales-stack/packages/ad-intel/`

**Import**:
```python
import sys
sys.path.insert(0, '/Users/shuvrajit/projects/tiro/open-sales-stack/packages/ad-intel')
from tools.meta_ads import ad_intel_meta_search
from tools.linkedin_ads import ad_intel_linkedin_search
```

**Tool 1: Meta Ad Library**
```python
async def ad_intel_meta_search(
    query: str,
    country: str = "US",
    ad_type: str = "all",  # "all", "political_and_issue_ads", "housing_ads", "employment_ads", "credit_ads"
    start_date_min: str | None = None,
    start_date_max: str | None = None,
) -> str  # JSON with {"total_result_count": str, "ads": [...], "search_url": str, "summary": str}
```
- Pre-checks for zero results before calling LLM (saves tokens)
- Uses crawl4ai + LLM extraction
- 3-second internal delay before HTML return
- Requires `LLM_API_KEY` env var

**Tool 2: LinkedIn Ad Library**
```python
async def ad_intel_linkedin_search(
    account_owner: str | None = None,
    payer: str | None = None,
    keyword: str | None = None,
    countries: str | None = None,
    date_option: str | None = None,  # "last-30-days", "current-month", "current-year", "last-year", "custom-date-range"
    start_date: str | None = None,
    end_date: str | None = None,
    impressions_min_value: int | None = None,
    impressions_max_value: int | None = None,
) -> str  # JSON with {"total_result_count": str, "ad_formats": [], "themes": [], "cta_buttons": [], ...}
```
- At least one of `account_owner`, `payer`, or `keyword` must be provided
- Requires `LLM_API_KEY` env var

---

## Data Sources & API Calls Per Account

For each account, the pipeline runs these steps. Each step is independent — if step 2 fails, step 1 and step 3 results are still saved.

### Step 1: Coresignal Company Enrich

**API**: `GET https://api.coresignal.com/cdapi/v2/company_multi_source/enrich?website={website_url}`

**Headers**: `{"Content-Type": "application/json", "apikey": CORESIGNAL_API_KEY}`

**Response**: Save the ENTIRE raw response JSON to `data/{domain}/coresignal.json` as-is. Do not transform it.

The Coresignal response is very rich. Key data it contains (for reference, not exhaustive):

**Company basics:**
- `company_name`, `company_legal_name`, `company_name_alias[]`
- `website`, `website_domain`, `linkedin_url`, `facebook_url[]`, `twitter_url[]`
- `description`, `description_enriched`
- `industry`, `categories_and_keywords[]`
- `founded_year`, `type`, `status`
- `is_b2b`, `is_public`

**Size & location:**
- `employees_count`, `size_range`
- `hq_country`, `hq_city`, `hq_state`, `hq_street`, `hq_zipcode`, `hq_full_address`
- `company_locations_full[]`

**Financials & funding:**
- `revenue_annual_range`, `revenue_annual`, `revenue_quarterly`
- `last_funding_round_name`, `last_funding_round_announced_date`, `last_funding_round_amount_raised`
- `funding_rounds[]`
- `income_statements[]`

**Tech stack:**
- `num_technologies_used`, `technologies_used[]` (with `technology`, `first_verified_at`, `last_verified_at`)

**Employee metrics (TIME SERIES — the data Apollo couldn't give us!):**
- `employees_count_by_month[]` — `{employees_count, date}`
- `employees_count_inferred_by_month[]` — `{employees_count_inferred, date}`
- `employees_count_breakdown_by_department` — current snapshot by dept
- `employees_count_breakdown_by_department_by_month[]` — monthly dept breakdown (36 months!)
- `employees_count_breakdown_by_seniority` — current snapshot by seniority
- `employees_count_breakdown_by_seniority_by_month[]` — monthly seniority breakdown
- `employees_count_breakdown_by_region` / `_by_month[]`
- `employees_count_by_country` / `_by_month[]`
- `departures_count_by_month[]`
- `employee_attrition_rate_by_month[]`
- `employees_count_change` — `{current, change_monthly, change_monthly_percentage, change_quarterly, change_quarterly_percentage}`

**Job postings:**
- `active_job_postings_count`, `active_job_postings[]`
- `active_job_postings_count_by_month[]`
- `active_job_postings_count_change`

**Social & web traffic:**
- `company_updates[]` — LinkedIn posts with engagement
- `followers_count_linkedin`, `linkedin_followers_count_by_month[]`
- `total_website_visits_monthly`, `total_website_visits_by_month[]`
- `bounce_rate`, `pages_per_visit`, `average_visit_duration_seconds`
- `visits_breakdown_by_country[]`

**Reviews & salary:**
- `company_employee_reviews_count`, `company_employee_reviews_aggregate_score`
- `employee_reviews_score_breakdown` — by category
- `employee_reviews_score_*_by_month[]` — time series for each review dimension
- `base_salary[]`, `additional_pay[]`, `total_salary[]`

**Competitive intel:**
- `competitors[]` — `{company_name, similarity_score}`
- `top_previous_companies[]`, `top_next_companies[]` — talent flow
- `key_executives[]`, `key_employee_change_events[]`

**Product signals:**
- `pricing_available`, `free_trial_available`, `demo_available`
- `is_downloadable`, `mobile_apps_exist`, `online_reviews_exist`, `documentation_exist`
- `product_reviews_count`, `product_reviews_aggregate_score`

### Step 2: Website Intel — Multiple Small Requests

**IMPORTANT: Make multiple small, targeted requests to website_intel_extract, NOT one large request.**

Save all results combined into `data/{domain}/website.json`.

Each sub-request has its own schema and prompt:

**2a. Pricing page detection**
```python
schema = {
    "type": "object",
    "properties": {
        "has_public_pricing": {"type": "boolean"},
        "pricing_model": {"type": "string"},  # "per_seat", "usage_based", "tiered", "flat_rate", "contact_us_only"
        "pricing_url": {"type": "string"},
        "lowest_visible_price": {"type": "string"},
        "has_free_tier": {"type": "boolean"},
        "has_free_trial": {"type": "boolean"},
        "trial_length_days": {"type": "integer"},
        "credit_card_required": {"type": "boolean"}
    }
}
prompt = "Find the pricing page. Extract whether pricing is publicly visible, the pricing model, lowest visible price, and whether there's a free trial or free tier."
mode = "crawl", limit = 3
```

**2b. Signup/demo form analysis**
```python
schema = {
    "type": "object",
    "properties": {
        "primary_cta": {"type": "string"},
        "form_field_count": {"type": "integer"},
        "form_fields": {"type": "array", "items": {"type": "string"}},
        "self_serve_signup": {"type": "boolean"},
        "requires_work_email": {"type": "boolean"}
    }
}
prompt = "Find the main signup or demo request form. Count the fields, list them, and determine if the user can self-serve into the product or must talk to sales."
mode = "scrape", limit = 1
```

**2c. Chatbot detection**
```python
schema = {
    "type": "object",
    "properties": {
        "has_chatbot": {"type": "boolean"},
        "chatbot_provider": {"type": "string"},
        "chatbot_can_book_meeting": {"type": "boolean"},
        "chatbot_type": {"type": "string"}  # "ai", "rule_based", "live_agent", "unknown"
    }
}
prompt = "Check if there's a chatbot or live chat widget on the homepage. Identify the provider and whether it can book meetings."
mode = "scrape", limit = 1
```

**2d. Homepage CTA analysis**
```python
schema = {
    "type": "object",
    "properties": {
        "homepage_cta_count": {"type": "integer"},
        "primary_cta_text": {"type": "string"},
        "secondary_cta_text": {"type": "string"},
        "has_interactive_demo": {"type": "boolean"},
        "interactive_demo_provider": {"type": "string"}
    }
}
prompt = "Analyze the homepage. Count distinct call-to-action buttons, identify the primary and secondary CTA text, and check for interactive product demos (Navattic, Storylane, etc.)."
mode = "scrape", limit = 1
```

**2e. GTM model inference**
```python
schema = {
    "type": "object",
    "properties": {
        "gtm_model": {"type": "string"},  # "product_led", "sales_led", "hybrid"
        "evidence": {"type": "array", "items": {"type": "string"}},
        "has_docs_or_api": {"type": "boolean"},
        "has_community": {"type": "boolean"}
    }
}
prompt = "Determine if this company is product-led (self-serve signup, docs, API-first), sales-led (demo/contact only), or hybrid. List evidence for your assessment."
mode = "crawl", limit = 3
```

### Step 3: Job Posting AI Check

Coresignal already provides `active_job_postings[]` in the response. After Step 1 completes:

1. From the Coresignal response, filter `active_job_postings` to only sales/GTM/marketing-related roles. Match titles containing (case-insensitive): `sales`, `sdr`, `bdr`, `account executive`, `ae`, `business development`, `revenue`, `gtm`, `go-to-market`, `demand gen`, `growth`, `marketing`, `partnerships`, `customer success`, `solutions engineer`, `se`, `pre-sales`, `revops`, `sales ops`, `sales engineer`

2. For each matching role that has a URL, use `website_intel_extract` to scrape the job posting URL and determine if it mentions AI tools:
```python
schema = {
    "type": "object",
    "properties": {
        "mentions_ai_tools": {"type": "boolean"},
        "ai_tools_mentioned": {"type": "string"},
        "role_title": {"type": "string"},
        "role_summary": {"type": "string"}
    }
}
prompt = "Read this job posting. Does it mention any AI tools, AI-powered platforms, or AI capabilities as part of the role's responsibilities or required skills? List the specific AI tools or AI features mentioned. Examples: AI SDR tools, AI email writers, ChatGPT, AI chatbots, AI forecasting, conversation intelligence, AI-powered CRM features, etc."
mode = "scrape", limit = 1
```

3. Save results into the `website.json` under an `ai_job_checks` key.

4. Aggregate into two account-level fields:
   - `sales_roles_mention_ai_tools` (boolean): true if ANY sales/GTM role mentions AI tools
   - `ai_tools_in_sales_roles` (string): pipe-separated list of all AI tools found

5. If a company has many matching roles (30+), cap AI checks at 20 — log the remainder as SKIPPED.

### Step 4: Ad Intel

Save results to `data/{domain}/ads.json`.

**4a. LinkedIn ads:**
```python
await ad_intel_linkedin_search(
    account_owner=company_name,
    date_option="last-30-days"
)
```

**4b. Meta ads:**
```python
await ad_intel_meta_search(
    query=company_name,
    country="US"
)
```

---

## Input / Output CSV Flow

### Input

The user provides a source CSV (Apollo account export). The key columns used by the pipeline:

- `Website` — the company URL, passed to Coresignal as the `website` param and used to derive the domain for the data directory name
- `Company Name` — used for ad searches and logging

**On first run, the pipeline adds a `pipeline_status` column to this source CSV** with values: `not_started`, `completed`, `partial`, `failed`. This column is updated in-place after each account is processed. This is the primary resume mechanism — on restart, skip rows where `pipeline_status == "completed"`.

**Deriving domain from Website column**: Extract the domain from the URL (e.g., `http://www.daytona.io` → `daytona.io`). Use this as the directory name under `data/`. Handle edge cases: strip `www.`, handle trailing slashes, handle missing protocol.

### Output

The compiler reads all `data/*/coresignal.json`, `data/*/website.json`, `data/*/ads.json` files and produces CSVs in `output/`.

---

## Rate Limiting

**Coresignal API:**
- No documented per-minute rate limit, but be respectful. Default: 1 request/second.

**Website-Intel (crawl4ai + LLM):**
- These hit external websites + an LLM provider. Rate limit to **3-second delay** between requests.
- No concurrent website-intel requests per account (run them sequentially within an account).

**Ad-Intel (crawl4ai + LLM):**
- Same as website-intel: **3-second delay** between requests.

**Implementation**: Use a simple `asyncio.sleep()` after each call. Put delay values in `config.py` so they're easy to tune:

```python
# config.py
CORESIGNAL_DELAY_SECONDS = 1.0      # 1 req/sec
WEBSITE_INTEL_DELAY_SECONDS = 3      # Respectful crawling + LLM rate limits
AD_INTEL_DELAY_SECONDS = 3           # Same as website-intel
MAX_RETRIES = 5                      # Retry transient failures up to 5 times
RETRY_BACKOFF_BASE = 2               # Exponential backoff: 2s, 4s, 8s, 16s, 32s
```

---

## Retry Logic

Retry up to **5 times** with exponential backoff for retryable errors:

**Retryable errors** (retry up to 5 times):
- HTTP 429 (rate limited) — backoff: `RETRY_BACKOFF_BASE ** attempt` seconds
- HTTP 500, 502, 503, 504 (server errors)
- `TimeoutError`, `ConnectionError`, `ConnectionResetError`
- `asyncio.TimeoutError`
- JSON decode errors from crawler (transient LLM failures)

**Non-retryable errors** (fail immediately, log, move on):
- HTTP 401, 403 (auth errors)
- HTTP 404 (resource not found — company not in Coresignal)
- HTTP 422 (validation error — bad input)
- `ValueError` from bad domain input

**Implementation**:
```python
async def with_retry(func, *args, max_retries=5, backoff_base=2, **kwargs):
    for attempt in range(max_retries + 1):
        try:
            result = await func(*args, **kwargs)
            return result
        except RETRYABLE_ERRORS as e:
            if attempt == max_retries:
                raise
            wait = backoff_base ** attempt
            log(f"Retry {attempt+1}/{max_retries} after {wait}s: {e}")
            await asyncio.sleep(wait)
    raise MaxRetriesExceeded(...)
```

---

## Per-Account Logging

For EVERY account, create a log file at `data/{domain}/account.log`:

```
[2026-03-20 14:23:01] START processing daytona.io (Company: Daytona)
[2026-03-20 14:23:01] STEP 1: Coresignal enrich — STARTED
[2026-03-20 14:23:02] STEP 1: Coresignal enrich — SUCCESS (67 employees, Telecommunications, 14 technologies)
[2026-03-20 14:23:02] STEP 2a: Website pricing — STARTED
[2026-03-20 14:23:10] STEP 2a: Website pricing — SUCCESS (public pricing: true, model: per_seat)
[2026-03-20 14:23:10] STEP 2b: Website signup form — STARTED
[2026-03-20 14:23:15] STEP 2b: Website signup form — FAILED attempt 1/5 (TimeoutError: page load exceeded 60s)
[2026-03-20 14:23:17] STEP 2b: Website signup form — RETRY 2/5 after 2s
[2026-03-20 14:23:22] STEP 2b: Website signup form — SUCCESS (4 fields, self-serve: true)
[2026-03-20 14:23:22] STEP 2c: Website chatbot — STARTED
...
[2026-03-20 14:23:50] STEP 3: Job posting AI check — STARTED (3 sales/GTM roles found)
[2026-03-20 14:23:55] STEP 3: Job posting AI check (1/3) "Head of Sales" — SUCCESS (mentions_ai: true, tools: "Gong AI")
[2026-03-20 14:24:00] STEP 3: Job posting AI check (2/3) "SDR" — SUCCESS (mentions_ai: false)
[2026-03-20 14:24:05] STEP 3: Job posting AI check (3/3) "Marketing Manager" — FAILED (all 5 retries exhausted)
[2026-03-20 14:24:05] STEP 4a: LinkedIn ads — STARTED
[2026-03-20 14:24:12] STEP 4a: LinkedIn ads — SUCCESS (5 active ads)
[2026-03-20 14:24:12] STEP 4b: Meta ads — STARTED
[2026-03-20 14:24:18] STEP 4b: Meta ads — SUCCESS (0 ads)
[2026-03-20 14:24:18] COMPLETE daytona.io — 8/9 steps succeeded, 1 failed [job_ai_check_3]
```

Each log entry includes:
- Timestamp
- Step name
- Status: STARTED, SUCCESS, FAILED, SKIPPED, RETRY
- On SUCCESS: brief summary of key data points
- On FAILED: error type + message (include which retry attempt if retries were used)
- On SKIPPED: reason (e.g., "no active_job_postings in Coresignal response")

---

## Raw Data File Format

### `data/{domain}/coresignal.json`
The ENTIRE raw Coresignal API response, dumped as-is. No transformation.

### `data/{domain}/website.json`
```json
{
  "pricing": { "has_public_pricing": true, "pricing_model": "per_seat", ... },
  "form": { "form_field_count": 4, "self_serve_signup": true, ... },
  "chatbot": { "has_chatbot": true, "chatbot_provider": "Drift", ... },
  "cta": { "homepage_cta_count": 3, "primary_cta_text": "Start Free Trial", ... },
  "gtm": { "gtm_model": "product_led", "evidence": [...], ... },
  "ai_job_checks": [
    {
      "title": "Head of Sales",
      "url": "https://...",
      "result": { "mentions_ai_tools": true, "ai_tools_mentioned": "Gong AI, Apollo AI" }
    }
  ]
}
```
Null values for any sub-key indicate a failed step.

### `data/{domain}/ads.json`
```json
{
  "linkedin": { "total_result_count": "5", "ad_formats": [...], ... },
  "meta": { "total_result_count": "0", "ads": [], ... }
}
```

**Critical**: Write each JSON file immediately after that step completes. Also update the `pipeline_status` column in the source CSV after ALL steps for an account finish. This is the checkpoint mechanism — if the pipeline crashes mid-account, partial data is already on disk.

---

## Resume Logic

When the script starts:
1. Read the source CSV
2. For `--all` mode: skip rows where `pipeline_status == "completed"`. Re-process `partial` and `failed`.
3. For `--retry-failed` mode: only process rows where `pipeline_status` is `partial` or `failed`. For `partial` accounts, check which JSON files exist in `data/{domain}/` and which sub-keys are non-null, then only re-run the missing steps.
4. For `--domain` mode: always process that domain (overwrite previous data).

---

## Column Schema for master.csv

### From Coresignal (flattened):
- `company_name`
- `company_legal_name`
- `domain` (from `website_domain`)
- `website`
- `linkedin_url`
- `industry`
- `categories_and_keywords` (pipe-separated)
- `type` (Self-Owned, etc.)
- `status`
- `is_b2b`
- `is_public`
- `founded_year`
- `employees_count`
- `employees_count_inferred`
- `size_range`
- `employees_count_change_monthly_pct`
- `employees_count_change_quarterly_pct`
- `departures_count`
- `employee_attrition_rate`
- `hq_country`
- `hq_city`
- `hq_state`
- `hq_full_address`
- `description` (truncated to 500 chars for CSV)
- `revenue_annual`
- `revenue_annual_range` (pipe-separated source values)
- `last_funding_round_name`
- `last_funding_round_announced_date`
- `last_funding_round_amount_raised`
- `last_funding_round_amount_raised_currency`
- `funding_rounds_count` (len of `funding_rounds[]`)
- `num_technologies_used`
- `technologies_used` (pipe-separated tech names)
- `followers_count_linkedin`
- `linkedin_followers_change_monthly_pct`
- `total_website_visits_monthly`
- `visits_change_monthly`
- `bounce_rate`
- `pages_per_visit`
- `average_visit_duration_seconds`
- `company_employee_reviews_count`
- `company_employee_reviews_aggregate_score`
- `active_job_postings_count`
- `active_job_postings_change_monthly_pct`
- `pricing_available` (from Coresignal product signals)
- `free_trial_available` (from Coresignal)
- `demo_available` (from Coresignal)
- `competitors` (pipe-separated company names)
- `key_executives` (pipe-separated "Name - Title")

### From Coresignal — department headcounts (latest snapshot):
- `employees_count_sales`
- `employees_count_engineering`
- `employees_count_marketing`
- `employees_count_hr`
- `employees_count_support`
- `employees_count_operations`
- `employees_count_finance`
- `employees_count_product`
- `employees_count_data_science`
- `employees_count_legal`

### From Coresignal — seniority breakdown (latest snapshot):
- `employees_count_clevel`
- `employees_count_vp`
- `employees_count_director`
- `employees_count_manager`
- `employees_count_senior`
- `employees_count_entry`

### From Job Posting AI Checks:
- `sales_gtm_job_postings_count`
- `sales_gtm_role_titles` (pipe-separated)
- `sales_roles_mention_ai_tools` (boolean)
- `ai_tools_in_sales_roles` (pipe-separated)

### From Website-Intel:
- `has_public_pricing`
- `pricing_model`
- `lowest_visible_price`
- `has_free_tier`
- `has_free_trial`
- `trial_length_days`
- `credit_card_required`
- `primary_cta`
- `form_field_count`
- `form_fields` (pipe-separated)
- `self_serve_signup`
- `requires_work_email`
- `has_chatbot`
- `chatbot_provider`
- `chatbot_can_book_meeting`
- `chatbot_type`
- `homepage_cta_count`
- `has_interactive_demo`
- `interactive_demo_provider`
- `gtm_model`
- `gtm_evidence` (pipe-separated)
- `has_docs_or_api`
- `has_community`

### From Ad-Intel:
- `linkedin_ad_count`
- `has_active_linkedin_ads` (boolean)
- `meta_ad_count`
- `has_active_meta_ads` (boolean)

### Processing metadata:
- `pipeline_status` (completed/partial/failed)
- `processing_date`
- `steps_succeeded` (count)
- `steps_failed` (count)
- `failed_steps` (pipe-separated list)

### Supplementary CSVs (long format, for charts/analysis):

**employee_trends.csv**: `domain, date, employees_count, employees_count_inferred, departures_count, attrition_rate` — one row per domain × month. From `employees_count_by_month`, `departures_count_by_month`, `employee_attrition_rate_by_month`.

**employee_dept_trends.csv**: `domain, date, department, count` — one row per domain × month × department. From `employees_count_breakdown_by_department_by_month`. This is the time series data for department growth charts.

**funding_events.csv**: `domain, round_name, announced_date, amount_raised, currency, lead_investors, num_investors`

**technologies.csv**: `domain, technology, first_verified_at, last_verified_at` — one row per domain × technology.

**keywords.csv**: `domain, keyword` — one row per domain × keyword. For word clouds.

**job_postings.csv**: `domain, title, url, location, is_sales_gtm, mentions_ai_tools, ai_tools_mentioned`

**processing_log.csv**: `domain, status, started_at, completed_at, steps_succeeded, steps_failed, failed_steps, error_summary`

---

## CLI Interface

```bash
# Process all unfinished accounts from the source CSV
python pipeline.py --file accounts.csv --all

# Process a single account by domain
python pipeline.py --file accounts.csv --domain daytona.io

# Retry only failed/partial accounts
python pipeline.py --file accounts.csv --retry-failed

# Dry run — show what would be processed
python pipeline.py --file accounts.csv --all --dry-run

# Compile CSVs from raw data (can run anytime, independently)
python compiler.py

# Show progress stats
python pipeline.py --file accounts.csv --stats
```

`--stats` output:
```
Total accounts in CSV: 3,500
Completed: 1,247 (35.6%)
Partial: 23 (0.7%)
Failed: 5 (0.1%)
Not started: 2,225 (63.6%)
Estimated time remaining: ~18.5 hours at current rate
```

---

## Error Handling Rules

1. **Never let one step's failure kill the entire account.** Wrap each step in try/except, log the error, save null for that step in the JSON, continue to next step.
2. **Never let one account's failure stop the pipeline.** Log it, update source CSV status, move to next account.
3. **Retry transient errors up to 5 times** with exponential backoff (see Retry Logic above).
4. **On non-retryable errors**: log immediately, save null, continue.
5. **On malformed JSON from website-intel or ad-intel**: log raw response string in a `_raw_error` field in the JSON, continue.
6. **If Coresignal returns 404 (company not found)**: log as SKIPPED, still proceed with website-intel and ad-intel using the domain/company name from the CSV.
7. **If Coresignal returns no `active_job_postings`**: skip the job posting AI check step (log as SKIPPED with reason).
8. **If no website URL available**: skip all website-intel steps (log as SKIPPED).

---

## Environment Variables (.env.example)

```
CORESIGNAL_API_KEY=
LLM_API_KEY=
LLM_PROVIDER=openai/gpt-5-mini-2025-08-07

# Rate limiting
CORESIGNAL_DELAY_SECONDS=1.0
WEBSITE_INTEL_DELAY_SECONDS=3
AD_INTEL_DELAY_SECONDS=3

# Retry
MAX_RETRIES=5
RETRY_BACKOFF_BASE=2
```

---

## Dependencies (requirements.txt)

```
httpx
python-dotenv
tqdm
```

Plus the transitive dependencies of `website-intel` and `ad-intel` (crawl4ai). The script should check for missing deps on startup and print install instructions.

---

## Implementation Notes

1. **sys.path manipulation**: Add the website-intel and ad-intel packages to `sys.path` before importing. Do this at the top of `processors/website.py` and `processors/ads.py`.
2. **All crawler functions are async** — the main pipeline loop must use `asyncio.run()` with an async main function.
3. **Crawler functions return JSON strings** — always `json.loads()` the result.
4. **Coresignal API returns JSON dicts** — standard `httpx` response handling.
5. **Write each JSON file immediately after that step completes** — this is the checkpoint mechanism. Update source CSV status after all steps for an account finish.
6. **The compiler is a separate script** — it reads all `data/*/` directories and outputs CSVs. Can be run at any time.
7. **tqdm progress bar** showing overall progress across all accounts.
8. **For job posting AI checks**: these go through website-intel (scraping external job board URLs). Rate limit them at the same `WEBSITE_INTEL_DELAY_SECONDS` pace. Cap at 20 roles per company.
9. **Use pipe `|` as delimiter** for multi-value fields in the master CSV (not comma, since values themselves may contain commas).
10. **Domain extraction from Website column**: Use `urllib.parse.urlparse` + `tldextract` to get the clean domain. Strip `www.` prefix. This domain becomes the directory name.
11. **Create data directory**: `os.makedirs(f"data/{domain}", exist_ok=True)` before writing any files for an account.
