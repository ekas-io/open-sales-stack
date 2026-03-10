# Website Intel

**Part of [Open Sales Stack](https://github.com/ekas-io/open-sales-stack) by [Ekas](https://ekas.io)**

MCP server that scrapes any website and extracts structured data as JSON using a custom schema. Handles JavaScript-heavy SPAs, dynamic content, and multi-page crawling.

**[Use cases and examples →](https://ekas.io/open-sales-stack/website-intel)**

---

## Tools

### `crawler_get_structured_info`

Scrape or crawl a webpage and extract structured data matching your JSON schema.

**Inputs:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `url` | string | Yes | Full URL to scrape (e.g. `https://example.com/pricing`) |
| `schema` | object | Yes | JSON Schema defining the shape of data to extract |
| `prompt` | string | Yes | Natural language instruction for what to extract |
| `mode` | `"scrape"` \| `"crawl"` | No | Single page (default) or follow links |
| `limit` | number | No | Max pages for crawl mode (default 5, max 10) |

**Example — extract pricing tiers:**

```
You: "Scrape acmecorp.com/pricing and extract their pricing tiers
      with tier name, price, and included features"

Claude calls: crawler_get_structured_info({
  url: "https://acmecorp.com/pricing",
  schema: {
    type: "object",
    properties: {
      tiers: {
        type: "array",
        items: {
          type: "object",
          properties: {
            name: { type: "string" },
            price: { type: "string" },
            features: { type: "array", items: { type: "string" } }
          }
        }
      }
    }
  },
  prompt: "Extract all pricing tiers with name, monthly price, and features"
})
```

**Example — multi-page crawl:**

```
You: "Crawl acmecorp.com's blog and extract the last 5 post titles and dates"

Claude uses mode: "crawl", limit: 5
```

---

## Setup

### Prerequisites

- macOS (Windows/Linux support planned)
- Node.js 20+
- Python 3.10+

### Install via Open Sales Stack (recommended)

```bash
# From the root of open-sales-stack:
npm run setup
# Add your OpenAI key to the root .env:
nano .env
```

### Environment variables

Configured in the root `.env` (shared by all MCPs). You can also create a `packages/website-intel/.env` to override values for this package only.

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | Yes | API key for LLM-based data extraction |
| `LLM_PROVIDER` | No | Defaults to `openai/gpt-5-mini-2025-08-07` |

### Add to Claude

```bash
# From the repo root:
bash scripts/add-to-claude.sh --website-intel
```

Or manually:

```bash
claude mcp add oss-website-intel \
  -s user \
  -e OPENAI_API_KEY=your-api-key \
  -- .venv/bin/python packages/website-intel/server.py
```

---

## How it works

1. You ask Claude to extract data from a URL
2. Claude calls the `crawler_get_structured_info` tool
3. The tool sends the URL to the local extraction server
4. The server renders the page (full JavaScript execution), then uses an LLM to extract data matching your schema
5. Structured JSON is returned to Claude

All processing happens locally on your machine. The only external API call is to OpenAI for the LLM extraction step.

---

## Part of Open Sales Stack

This is one of several research MCPs. See the [full toolkit](https://github.com/ekas-io/open-sales-stack) or visit [ekas.io/open-sales-stack](https://ekas.io/open-sales-stack) for detailed use cases.
