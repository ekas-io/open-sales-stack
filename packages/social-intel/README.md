# Social Intel

**Part of [Open Sales Stack](https://github.com/ekas-io/open-sales-stack) by [Ekas](https://ekas.io)**

MCP server that scrapes LinkedIn profiles, companies, and company posts.

---

## Tools

### `scrape_linkedin_profile`

Scrape a LinkedIn profile and return structured data about the person.

**Inputs:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `linkedin_url` | string | Yes | LinkedIn profile URL (e.g. `https://www.linkedin.com/in/username/`) |

**Returns:** JSON object with name, headline, location, about, experiences, education, and skills.

---

### `scrape_linkedin_company`

Scrape a LinkedIn company page and return structured data.

**Inputs:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `linkedin_url` | string | Yes | LinkedIn company URL (e.g. `https://www.linkedin.com/company/company-name/`) |

**Returns:** JSON object with company name, industry, company size, headquarters, founded year, specialties, and overview.

---

### `scrape_linkedin_company_posts`

Scrape recent posts from a LinkedIn company page.

**Inputs:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `linkedin_url` | string | Yes | LinkedIn company URL (e.g. `https://www.linkedin.com/company/company-name/`) |

**Returns:** JSON array of post objects with text content, reaction counts, comment counts, repost counts, and posted dates.

---

## LinkedIn Authentication

A LinkedIn account is required. During `bash scripts/setup.sh`, you'll be prompted to choose one of three options:

### Option 1: Skip (default)

Skip LinkedIn authentication during setup. Company scraping still works without login. Profile scraping and posts require authentication — you can configure it later by re-running `bash scripts/setup.sh` or manually setting credentials in `packages/social-intel/.env`.

### Option 2: Browser Login

A browser window opens during setup. You log into LinkedIn manually, and the session is saved for future use. This is the most reliable method — it handles 2FA and CAPTCHAs naturally since you're logging in yourself.

### Option 3: Credentials

You provide your LinkedIn email and password during setup. They're saved to `packages/social-intel/.env` and used for automatic headless login. Faster for subsequent setups, but may fail if LinkedIn requires 2FA or CAPTCHA.

| Variable | Description |
|---|---|
| `LINKEDIN_EMAIL` | Your LinkedIn email address |
| `LINKEDIN_PASSWORD` | Your LinkedIn password |

### Session persistence

After the first login (either method), the session is saved to `packages/social-intel/linkedin_session.json`. Subsequent runs reuse this session without requiring login again. Delete the file to force a fresh login.

> **Note:** LinkedIn may occasionally invalidate sessions or require verification. If scraping stops working, delete `linkedin_session.json` and re-authenticate.

---

## Setup

### Prerequisites

- Python 3.10+
- A LinkedIn account

### Dependencies

Dependencies are **auto-installed** on first run. The server checks for required packages and the Chromium browser, installing them if missing.

### Add to Claude

```bash
# From the repo root:
bash scripts/add-to-claude.sh --social-intel
```

### Environment variables

Configured in the root `.env` or `packages/social-intel/.env`.

| Variable | Required | Description |
|---|---|---|
| `LINKEDIN_EMAIL` | No | LinkedIn email for programmatic login |
| `LINKEDIN_PASSWORD` | No | LinkedIn password for programmatic login |

---

## How it works

1. You ask Claude to research a person or company on LinkedIn
2. Claude calls one of the social-intel tools with the LinkedIn URL
3. The server authenticates with LinkedIn (session reuse, programmatic login, or manual login)
4. A headless browser loads the page and extracts structured data
5. JSON results are returned to Claude

All processing happens locally on your machine. No external APIs are called.

---

## Part of Open Sales Stack

This is one of several research MCPs. See the [full toolkit](https://github.com/ekas-io/open-sales-stack) or visit [ekas.io/open-sales-stack](https://ekas.io/open-sales-stack) for detailed use cases.
