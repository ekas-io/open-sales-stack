# techstack-intel

**Part of [Open Sales Stack](https://github.com/ekas-io/open-sales-stack) by [Ekas](https://ekas.io)**

MCP server that detects the technology stack used by a company website. Returns a structured JSON report with all detected technologies, confidence scores, and evidence trails.

---

## Tools

### `detect_techstack`

Detect the technology stack used by a company website.

**Inputs:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `url` | string | Yes | Company website URL (e.g. `https://example.com`) |

**Returns:** JSON report with detected technologies, each having `name`, `category`, `confidence` (0–1), `evidence`, and optional `version`.

**Detection methods:**
- HTTP response headers (web server, framework, CDN, hosting)
- HTML/DOM (CMS, JS frameworks, analytics, chat widgets, marketing tools)
- DNS records (email provider, DNS provider, hosted services)
- SSL certificates (certificate authority)
- robots.txt & sitemap.xml (CMS, SEO tools)
- Cookies (analytics, marketing, session technology)
- Favicon fingerprinting

---

## Testing

```bash
pytest packages/techstack-intel/tests/ -v -s

# Unit tests only (no network)
pytest packages/techstack-intel/tests/test_detectors_unit.py -v -s

# Integration tests (requires network, 5-15s each)
pytest packages/techstack-intel/tests/test_integration.py -v -s
```

---

## Setup

### Prerequisites

- Python 3.11+
- Dependencies: `httpx`, `dnspython`, `tldextract`

### Install via Open Sales Stack (recommended)

```bash
bash scripts/setup.sh
bash scripts/add-to-claude.sh --techstack-intel
```

### Add to Claude

```bash
claude mcp add oss-techstack-intel -- python packages/techstack-intel/server.py
```

---

## Part of Open Sales Stack

This is one of several research MCPs. See the [full toolkit](https://github.com/ekas-io/open-sales-stack).
