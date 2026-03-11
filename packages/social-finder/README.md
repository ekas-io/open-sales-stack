# Social Finder

**Part of [Open Sales Stack](https://github.com/ekas-io/open-sales-stack) by [Ekas](https://ekas.io)**

MCP server that finds and extracts social profile data for companies and people across LinkedIn, Twitter/X, GitHub, Quora, and more.

**[Use cases and examples →](https://ekas.io/open-sales-stack/social-finder)**

---

## Tools

### `find_social_profiles`

Find social media profiles and extract public data for a person or company.

**Inputs:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `name` | string | Yes | Person or company name to look up |
| `company` | string | No | Company name (helps disambiguate people search) |

---

## Coverage

| Platform | Profile Type | Status |
|---|---|---|
| LinkedIn | Company profile (about, headcount, industry, founded) | ✅ Done |
| LinkedIn | Person profile (headline, bio, role history) | ✅ Done |
| LinkedIn | Company posts (recent activity, engagement) | ✅ Done |
| Twitter / X | Person/company profile (bio, followers, recent tweets) | 🔄 In Progress |
| GitHub | Person/org profile (repos, stars, contribution activity) | 🔄 In Progress |
| Quora | Person profile (topics, answers, expertise signals) | 🔄 In Progress |
| YouTube | Company channel (video activity, subscriber count) | 🔄 In Progress |
| Reddit | Person/community activity (relevant subreddits, posts) | 🔄 In Progress |

---

## Setup

### Prerequisites

- macOS (Windows/Linux support planned)
- Python 3.10+

### Install via Open Sales Stack (recommended)

```bash
# From the root of open-sales-stack:
bash scripts/setup.sh
bash scripts/add-to-claude.sh --social-finder
```

### Environment variables

Configured in the root `.env` (shared by all MCPs).

| Variable | Required | Description |
|---|---|---|
| `LLM_API_KEY` | Yes | API key for your chosen LLM provider |
| `LLM_PROVIDER` | Yes | Provider and model (e.g. `openai/gpt-4o-mini`) |

---

## How it works

1. You ask Claude to find profiles for a person or company
2. Claude calls `find_social_profiles`
3. The tool searches for public profile pages across platforms
4. crawl4ai renders the pages and extracts structured profile data using your configured LLM
5. Structured JSON is returned to Claude

All processing happens locally on your machine.

---

## Part of Open Sales Stack

This is one of several research MCPs. See the [full toolkit](https://github.com/ekas-io/open-sales-stack) or visit [ekas.io/open-sales-stack](https://ekas.io/open-sales-stack) for detailed use cases.
