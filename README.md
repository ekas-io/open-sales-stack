# ekas-mcps

Node.js boilerplate for a personal sales engine with shared business methods exposed as both REST and MCP endpoints.

## What this includes

- TypeScript + Express runtime with secure defaults.
- Shared method registry so one method implementation can be used by:
  - REST endpoints (`/api/:domain/:method`)
  - MCP endpoint (`/mcp`, JSON-RPC)
- Domain-first structure: `data`, `crawler`, `crm`.
- API key auth middleware for all REST and MCP requests.
- Cloud Run deploy script (`npm run deploy`) that:
  - Reads local `.env`
  - Syncs secrets to Secret Manager
  - Deploys latest source to Cloud Run with cost controls (`min instances = 0`)

## Project structure

```text
src/
  app.ts
  index.ts
  config/
    env.ts
  lib/
    http-error.ts
    logger.ts
  middleware/
    api-key-auth.ts
  methods/
    create-hello-method.ts
    index.ts
    data/hello.ts
    crawler/hello.ts
    crm/hello.ts
    types.ts
  transports/
    rest/register-rest-routes.ts
    mcp/handle-mcp-request.ts
    mcp/register-mcp-route.ts
scripts/
  deploy.sh
```

## Quick start

1. Install dependencies:

```bash
npm install
```

2. Configure env:

```bash
cp .env.example .env
```

3. Generate a strong API key and set `API_KEY`:

```bash
openssl rand -hex 32
```

4. Run locally:

```bash
npm run dev
```

## REST usage

All requests need `x-api-key`.

List methods:

```bash
curl -s http://localhost:8080/api/methods \
  -H "x-api-key: <API_KEY>"
```

Call hello method:

```bash
curl -s http://localhost:8080/api/data/hello \
  -X POST \
  -H "content-type: application/json" \
  -H "x-api-key: <API_KEY>" \
  -d '{"name":"Shuvra"}'
```

## MCP usage

POST JSON-RPC to `/mcp` with `x-api-key`.

List tools:

```bash
curl -s http://localhost:8080/mcp \
  -X POST \
  -H "content-type: application/json" \
  -H "x-api-key: <API_KEY>" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

Call tool:

```bash
curl -s http://localhost:8080/mcp \
  -X POST \
  -H "content-type: application/json" \
  -H "x-api-key: <API_KEY>" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"data.hello","arguments":{"name":"Shuvra"}}}'
```

## Deploy to Cloud Run

1. Fill deploy values in `.env`:

- `GCP_PROJECT_ID`
- `CLOUD_RUN_SERVICE`
- `CLOUD_RUN_REGION`

2. Deploy:

```bash
npm run deploy
```

This script will:

- Enable required GCP APIs.
- Upsert each secret from local `.env` to Secret Manager.
- Deploy to Cloud Run with:
  - `min-instances=0` (no idle instance billing)
  - bounded `max-instances`
  - CPU throttling outside request handling

## Security notes

- API key required for all `/api/*` and `/mcp` calls.
- API key is compared with timing-safe equality.
- Secrets are injected from Secret Manager at runtime.
- Set `CLOUD_RUN_ALLOW_UNAUTHENTICATED=false` to require IAM auth at Cloud Run edge.
