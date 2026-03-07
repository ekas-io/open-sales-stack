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
- Python 3.10+ (for crawl4ai)

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
| `OPENAI_API_KEY` | Yes | Used by crawl4ai for LLM-based data extraction |
| `CRAWL4AI_BASE_URL` | No | Defaults to `http://localhost:11235` |

### Start the crawl4ai server

From the repo root:

```bash
npm run crawl4ai:start
```

Verify it's running:

```bash
curl http://localhost:11235/health
```

### Add to Claude

```bash
# From the repo root:
npm run add-to-claude -- --website-intel
```

Or manually for Claude Code:

```bash
claude mcp add oss-website-intel \
  -s user \
  -e OPENAI_API_KEY=sk-your-key \
  -e CRAWL4AI_BASE_URL=http://localhost:11235 \
  -- tsx /path/to/open-sales-stack/packages/website-intel/src/index.ts
```

---

## How it works

1. You ask Claude to extract data from a URL
2. Claude calls the `crawler_get_structured_info` tool
3. The tool sends the URL to your local crawl4ai server
4. crawl4ai renders the page (full JavaScript execution), then uses GPT-4o-mini to extract data matching your schema
5. Structured JSON is returned to Claude

All processing happens locally on your machine. The only external API call is to OpenAI for the LLM extraction step.

---

## Part of Open Sales Stack

This is one of several research MCPs. See the [full toolkit](https://github.com/ekas-io/open-sales-stack) or visit [ekas.io/open-sales-stack](https://ekas.io/open-sales-stack) for detailed use cases.
