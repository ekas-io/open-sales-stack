# review-intel

**Part of [Open Sales Stack](https://github.com/ekas-io/open-sales-stack) by [Ekas](https://ekas.io)**

MCP server for extracting review data from G2, Capterra, Glassdoor, and other review platforms.

> **Status: Not yet implemented.** See `packages/website-intel` for the extraction approach this will use.

---

## Tools

### `get_reviews`

Get review data for a company from review platforms.

**Inputs:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `company` | string | Yes | Company name to look up |
| `platform` | string | No | Review platform: `g2`, `capterra`, `glassdoor` (default: `g2`) |

---

## Testing

```bash
pytest packages/review-intel/tests/ -v -s
```

---

## Setup

```bash
bash scripts/setup.sh
bash scripts/add-to-claude.sh --review-intel
```

---

## Part of Open Sales Stack

This is one of several research MCPs. See the [full toolkit](https://github.com/ekas-io/open-sales-stack).
