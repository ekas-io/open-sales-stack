# hiring-intel

Search job postings across major job boards and extract job descriptions from career pages. Built for researching prospects and accounts — understand what a company is hiring for, identify growth areas, and find organizational signals.

## Tools

### `search_jobs`

Search for job postings across 6 job boards using [JobSpy](https://github.com/speedyapply/JobSpy).

**Supported job boards:**

| Job Board | Coverage | Notes |
|---|---|---|
| Indeed | Most countries (60+) | Best scraper — no rate limiting. Set `country_indeed` for non-US searches. |
| LinkedIn | Global | Rate-limits aggressively (~page 10 without proxies). Use `linkedin_company_ids` for targeted searches. |
| Glassdoor | Select countries | Set `country_indeed` for non-US. |
| Google Jobs | Global | Requires `google_search_term` with Google search syntax. |
| ZipRecruiter | US & Canada | — |
| Bayt | International | — |

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `search_term` | string | *required* | Keywords to search for (e.g. "software engineer", "sales development representative") |
| `site_name` | list[str] | all sites | Which job boards to search. Options: `linkedin`, `indeed`, `glassdoor`, `google`, `zip_recruiter`, `bayt` |
| `location` | string | — | City, state, or region (e.g. "San Francisco", "Texas", "London") |
| `distance` | int | 50 | Search radius in miles from location |
| `job_type` | string | — | Filter by type: `fulltime`, `parttime`, `internship`, `contract` |
| `is_remote` | bool | — | Filter for remote positions only |
| `results_wanted` | int | 10 | Number of results per site (capped at 50) |
| `hours_old` | int | — | Only show jobs posted within this many hours |
| `country_indeed` | string | — | Country for Indeed/Glassdoor (e.g. "UK", "Germany", "India") |
| `linkedin_fetch_description` | bool | false | Fetch full descriptions from LinkedIn (slower, more requests) |
| `linkedin_company_ids` | list[int] | — | Filter LinkedIn results by company IDs |
| `google_search_term` | string | — | Google search syntax query (required for Google Jobs) |
| `easy_apply` | bool | — | Only show job board-hosted applications |
| `enforce_annual_salary` | bool | false | Convert all salary figures to annual equivalents |
| `offset` | int | — | Skip this many results (pagination) |
| `description_format` | string | "markdown" | Format for job descriptions: `markdown` or `html` |

**Output fields per job:**

- `title`, `company_name`, `company_url`, `job_url`
- `location` (city, state, country)
- `is_remote`, `job_type`, `description`
- `date_posted`, `emails`
- Compensation: `min_amount`, `max_amount`, `currency`, `interval`
- LinkedIn-specific: `job_level`, `company_industry`
- Indeed-specific: `company_country`, `company_employees_label`, `company_revenue_label`

### `extract_job_description`

Extract the full content from a job posting URL or crawl a company's careers page.

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `url` | string | *required* | Job posting URL or company careers page URL |
| `mode` | string | "single" | `single` for one job URL, `crawl` for discovering listings on a careers page |
| `max_pages` | int | 5 | Maximum pages to crawl (only used in `crawl` mode, capped at 10) |

**Modes:**

- **single**: Fetches a single job posting URL and returns the content as markdown. Use when you have a specific job URL (e.g. from `search_jobs` results, Greenhouse/Lever links, etc.).
- **crawl**: Follows links on a company's careers page to discover and extract job listings. Use with a URL like `https://company.com/careers`.

**Limitations:**
- LinkedIn job URLs are blocked by LinkedIn's anti-scraping measures. Use `search_jobs` with `site_name=["linkedin"]` and `linkedin_fetch_description=true` instead.
- Works well with: company career sites, Greenhouse, Lever, Ashby, Workday, and most other ATS platforms.

## Environment Variables

Set these in your root `.env` file if needed:

| Variable | Required | Description |
|---|---|---|
| `JOBSPY_PROXIES` | No | Comma-separated list of proxy addresses for JobSpy. Format: `user:pass@host:port` or `host:port`. Proxies are rotated round-robin. |
| `JOBSPY_CA_CERT` | No | Path to a CA certificate file for proxy SSL connections. Only needed if your proxy uses a custom certificate authority. |

### When do you need proxies?

- **LinkedIn scraping at volume**: LinkedIn rate-limits around page 10 with a single IP. If you're doing heavy LinkedIn searches, proxies help distribute requests.
- **Corporate networks**: If your network uses SSL inspection, you may need `JOBSPY_CA_CERT` pointing to your corporate CA certificate.
- **Geo-targeted searches**: Proxies in specific regions can return localized results for that region.

For light research use (a few searches per session), you typically **don't need proxies**. Indeed works well without them.

### Example `.env` configuration

```bash
# Single proxy
JOBSPY_PROXIES=user:pass@proxy.example.com:8080

# Multiple proxies (round-robin rotation)
JOBSPY_PROXIES=user:pass@proxy1.example.com:8080,user:pass@proxy2.example.com:8080

# Corporate CA certificate
JOBSPY_CA_CERT=/path/to/corporate-ca.pem
```

## Good Practices

1. **Start with Indeed** — it has the best scraping reliability and no rate limiting. Use LinkedIn as a secondary source.
2. **Keep results low** — `results_wanted=10` to `25` is plenty for account research. This isn't a bulk scraping tool.
3. **Be specific** — search for a company name + role type rather than broad terms. This reduces noise and avoids unnecessary load on job boards.
4. **Use `hours_old`** — filter to recent postings (e.g. `hours_old=720` for last 30 days) to focus on active hiring signals.
5. **Use `linkedin_company_ids`** — when you know the exact company, this gives the most precise LinkedIn results.
6. **Respect rate limits** — if you get HTTP 429 errors, wait between searches. Don't retry immediately.
7. **Combine with other tools** — pair hiring data with `techstack-intel` to see what tech they're hiring for, or `website-intel` to extract team structure from their About page.

## Limitations

- **Not for bulk data collection** — this tool is designed for targeted prospect/account research, not building large job posting datasets. Keep your searches focused and results low.
- **All platforms cap at ~1000 results** per search query regardless of `results_wanted`.
- **LinkedIn aggressively rate-limits** — without proxies, expect blocking around page 10. Indeed is more reliable for volume.
- **Indeed filter combinations** — you cannot combine `hours_old` with `job_type` + `is_remote` in the same Indeed search.
- **LinkedIn filter combinations** — `hours_old` and `easy_apply` cannot be combined on LinkedIn.
- **Job descriptions vary** — some postings include full descriptions, others just titles and links. Use `extract_job_description` to fetch the full content when needed.
- **Geographic accuracy** — location-based results depend on how the employer tagged the posting. Remote jobs may show up under unexpected locations.
- **LinkedIn descriptions** — not included by default. Set `linkedin_fetch_description=true` to fetch them (increases request count and time).
- **Google Jobs** — requires `google_search_term` with Google search syntax; the regular `search_term` parameter is not used for Google.

## Example Usage

**Research what roles a company is hiring for:**
> "What jobs is Stripe hiring for right now?"

Claude will call `search_jobs(search_term="Stripe", results_wanted=15)` and summarize the open roles by department.

**Find engineering hires in a specific location:**
> "Show me backend engineering roles at companies in Austin, TX"

Claude will call `search_jobs(search_term="backend engineer", location="Austin, TX", job_type="fulltime")`.

**Get the full description for a specific job:**
> "Get me the full job description from this Greenhouse link"

Claude will call `extract_job_description(url="https://boards.greenhouse.io/company/jobs/12345")`.

**Discover all open roles from a company's careers page:**
> "Crawl Notion's careers page and show me what they're hiring for"

Claude will call `extract_job_description(url="https://notion.so/careers", mode="crawl", max_pages=10)`.
