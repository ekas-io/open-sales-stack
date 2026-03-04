import { z } from "zod";
import { env } from "../../config/env";
import type { Domain, MethodDefinition } from "../types";
import { logger } from "../../lib/logger";

/**
 * Input schema for the structured-info tool.
 *
 * Descriptions are intentionally verbose — they are surfaced as argument
 * descriptions inside the MCP tool definition so that calling agents
 * understand exactly what to provide.
 */
const getStructuredInfoInputSchema = z.object({
  url: z
    .string()
    .url("Must be a fully-qualified URL including protocol (https://…)")
    .describe(
      "The full URL of the webpage to scrape/crawl and extract structured data from. " +
        "Must be a valid, publicly accessible URL including the protocol " +
        "(e.g. 'https://example.com/pricing')."
    ),

  schema: z
    .record(z.any())
    .describe(
      "A valid JSON Schema object that defines the exact structure of the data you want extracted. " +
        "The returned JSON will match your specification exactly. " +
        "The root must be an object with 'type', 'properties', and optionally 'required'. " +
        "Use standard JSON Schema types: 'string', 'number', 'boolean', 'array', 'object'. " +
        "\n\n" +
        "Example — extract pricing tiers:\n" +
        '{\n' +
        '  "type": "object",\n' +
        '  "required": [],\n' +
        '  "properties": {\n' +
        '    "pricing_tiers": {\n' +
        '      "type": "array",\n' +
        '      "items": {\n' +
        '        "type": "object",\n' +
        '        "properties": {\n' +
        '          "tier_name": { "type": "string" },\n' +
        '          "price": { "type": "string" },\n' +
        '          "features": { "type": "array", "items": { "type": "string" } }\n' +
        "        }\n" +
        "      }\n" +
        "    }\n" +
        "  }\n" +
        "}\n\n" +
        "Example — extract team/contact info:\n" +
        '{\n' +
        '  "type": "object",\n' +
        '  "properties": {\n' +
        '    "team_members": {\n' +
        '      "type": "array",\n' +
        '      "items": {\n' +
        '        "type": "object",\n' +
        '        "properties": {\n' +
        '          "name": { "type": "string" },\n' +
        '          "role": { "type": "string" },\n' +
        '          "email": { "type": "string" }\n' +
        "        }\n" +
        "      }\n" +
        "    }\n" +
        "  }\n" +
        "}"
    ),

  prompt: z
    .string()
    .min(1, "prompt is required")
    .describe(
      "A clear, natural-language instruction telling the tool exactly what information " +
        "to extract from the page(s). Be as specific as possible about the data points you need. " +
        "Good examples:\n" +
        "  • 'Extract all pricing tiers including tier name, monthly price, annual price, and included features'\n" +
        "  • 'Find all team members with their names, job titles, and LinkedIn URLs'\n" +
        "  • 'Extract product announcements including title, date, and summary from the changelog'\n" +
        "  • 'Get all contact information: office addresses, phone numbers, and support emails'"
    ),

  mode: z
    .enum(["scrape", "crawl"])
    .default("scrape")
    .describe(
      "The extraction mode to use.\n\n" +
        "• 'scrape' (default) — Extracts data from the single URL provided. " +
        "Uses a stealth proxy so it works reliably on sites with anti-bot " +
        "protection (e.g. G2, Capterra, LinkedIn). Returns results immediately " +
        "(synchronous). Best for: extracting data from one specific page — " +
        "reviews, pricing, a company profile, etc. Costs up to 5 extra credits " +
        "per request due to the stealth proxy.\n\n" +
        "• 'crawl' — Starts from the given URL and follows links within the " +
        "same domain, scraping up to 'limit' pages. " +
        "Best for: gathering data spread " +
        "across multiple pages — paginated review lists, multi-page docs, " +
        "sitemaps, blog archives. Does NOT use a stealth proxy, so it may " +
        "return empty results on heavily-protected sites."
    ),

  limit: z
    .number()
    .int()
    .positive()
    .max(10)
    .default(5)
    .describe(
      "Maximum number of pages to crawl. Only used in 'crawl' mode. " +
        "Defaults to 5, max is 10. Set to 1 if you only need data from the " +
        "exact URL provided. Increase if the information might span multiple " +
        "pages (e.g. paginated lists, multi-page docs). Higher values " +
        "increase crawl time. Ignored in 'scrape' mode."
    ),
});

type GetStructuredInfoOutput = {
  data: unknown;
  status: string;
  metadata?: unknown;
  crawlId?: string;
  totalPages?: number;
  timestamp: string;
};

const FIRECRAWL_BASE_URL = "https://api.firecrawl.dev/v2";
const POLL_INTERVAL_MS = 5_000;
const MAX_POLL_ATTEMPTS = 120; // 10 minutes max

/**
 * Helper: sleep for a given number of milliseconds.
 */
function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/* ─── Shared helpers ──────────────────────────────────────────────────── */

function firecrawlHeaders(): Record<string, string> {
  return {
    Authorization: `Bearer ${env.FIRECRAWL_API_KEY}`,
    "Content-Type": "application/json",
  };
}

function jsonFormat(schema: Record<string, unknown>, prompt: string) {
  return { type: "json" as const, schema, prompt };
}

/** Remove statusCode and error from metadata — do not expose to callers. */
function sanitizeMetadata(metadata: unknown): unknown {
  if (!metadata || typeof metadata !== "object") return metadata;
  const { statusCode: _sc, error: _err, ...rest } = metadata as Record<string, unknown>;
  return rest;
}

/* ─── Scrape (single page, basic first → stealth retry) ───────────────── */

type ScrapeResult = {
  success: boolean;
  data?: {
    json?: unknown;
    metadata?: unknown;
    markdown?: string;
  };
  error?: string;
  code?: string;
};

/**
 * Calls the Firecrawl /scrape endpoint with the given proxy setting.
 * Returns the parsed JSON body — does NOT throw on `success: false`
 * so the caller can decide whether to retry.
 */
async function callScrape(
  input: z.infer<typeof getStructuredInfoInputSchema>,
  proxy: "basic" | "stealth",
): Promise<ScrapeResult> {
  const body: Record<string, unknown> = {
    url: input.url,
    timeout: 120_000,
    formats: [jsonFormat(input.schema, input.prompt)],
    proxy,
  };

  // stealth proxy handles ad-blocked sites better without blockAds
  if (proxy === "stealth") {
    body.blockAds = false;
  }

  const response = await fetch(`${FIRECRAWL_BASE_URL}/scrape`, {
    method: "POST",
    headers: firecrawlHeaders(),
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const errorText = await response.text();
    return { success: false, error: `HTTP ${response.status}: ${errorText}` };
  }

  return (await response.json()) as ScrapeResult;
}

async function executeScrape(
  input: z.infer<typeof getStructuredInfoInputSchema>
): Promise<GetStructuredInfoOutput> {
  // ── 1. Try with basic proxy (cheap) ────────────────────────────────
  logger.info(
    { url: input.url, mode: "scrape", proxy: "basic" },
    "Starting Firecrawl scrape (basic proxy)"
  );

  const basicResult = await callScrape(input, "basic");

  // Return data if present — even when success is false (e.g. target page
  // returned 403) Firecrawl may still extract valid JSON from cached/partial content.
  if (basicResult.data?.json) {
    logger.info(
      { url: input.url, proxy: "basic", hasJson: true, apiSuccess: basicResult.success },
      "Firecrawl scrape returned data with basic proxy"
    );

    return {
      data: basicResult.data.json,
      metadata: sanitizeMetadata(basicResult.data.metadata),
      status: "completed",
      timestamp: new Date().toISOString(),
    };
  }

  // ── 2. Basic returned no data — retry with stealth ─────────────────
  logger.info(
    { url: input.url, basicError: basicResult.error ?? basicResult.code ?? "empty json" },
    "Basic proxy returned no data, retrying with stealth proxy"
  );

  const stealthResult = await callScrape(input, "stealth");

  // Same as above: prefer extracted data even if success flag is false.
  if (stealthResult.data?.json) {
    logger.info(
      { url: input.url, proxy: "stealth", hasJson: true, apiSuccess: stealthResult.success },
      "Firecrawl scrape returned data with stealth proxy"
    );

    return {
      data: stealthResult.data.json,
      metadata: sanitizeMetadata(stealthResult.data.metadata),
      status: "completed",
      timestamp: new Date().toISOString(),
    };
  }

  // Both proxies returned no extractable data — throw.
  throw new Error(
    `Firecrawl scrape failed (both basic and stealth): ${stealthResult.error ?? basicResult.error ?? JSON.stringify(stealthResult)}`
  );
}

/* ─── Crawl (multi-page, async polling) ───────────────────────────────── */

async function executeCrawl(
  input: z.infer<typeof getStructuredInfoInputSchema>
): Promise<GetStructuredInfoOutput> {
  const body = {
    url: input.url,
    sitemap: "include",
    crawlEntireDomain: false,
    limit: input.limit,
    scrapeOptions: {
      onlyMainContent: false,
      maxAge: 172_800_000, // 48 hours cache
      parsers: ["pdf"],
      formats: [jsonFormat(input.schema, input.prompt)],
    },
  };

  logger.info(
    { url: input.url, limit: input.limit, mode: "crawl" },
    "Starting Firecrawl crawl"
  );

  // 1. Kick off the crawl
  const crawlResponse = await fetch(`${FIRECRAWL_BASE_URL}/crawl`, {
    method: "POST",
    headers: firecrawlHeaders(),
    body: JSON.stringify(body),
  });

  if (!crawlResponse.ok) {
    const errorText = await crawlResponse.text();
    throw new Error(
      `Firecrawl API error (${crawlResponse.status}): ${errorText}`
    );
  }

  const crawlData = (await crawlResponse.json()) as {
    success: boolean;
    id?: string;
  };

  if (!crawlData.success || !crawlData.id) {
    throw new Error(
      `Firecrawl crawl initiation failed: ${JSON.stringify(crawlData)}`
    );
  }

  const crawlId = crawlData.id;
  logger.info({ crawlId }, "Firecrawl crawl started, polling for results");

  // 2. Poll until complete
  for (let attempt = 0; attempt < MAX_POLL_ATTEMPTS; attempt++) {
    await sleep(POLL_INTERVAL_MS);

    const statusResponse = await fetch(
      `${FIRECRAWL_BASE_URL}/crawl/${crawlId}`,
      {
        method: "GET",
        headers: {
          Authorization: `Bearer ${env.FIRECRAWL_API_KEY}`,
        },
      }
    );

    if (!statusResponse.ok) {
      const errorText = await statusResponse.text();
      throw new Error(
        `Firecrawl status check error (${statusResponse.status}): ${errorText}`
      );
    }

    const statusData = (await statusResponse.json()) as {
      status: string;
      data?: unknown[];
      total?: number;
    };

    if (statusData.status === "completed") {
      logger.info(
        { crawlId, pages: statusData.data?.length ?? 0 },
        "Firecrawl crawl completed"
      );

      return {
        data: statusData.data,
        status: "completed",
        crawlId,
        totalPages: statusData.total ?? statusData.data?.length ?? 0,
        timestamp: new Date().toISOString(),
      };
    }

    if (
      statusData.status === "failed" ||
      statusData.status === "cancelled"
    ) {
      throw new Error(
        `Firecrawl crawl ${statusData.status}: ${JSON.stringify(statusData)}`
      );
    }

    // Still in progress — keep polling
    logger.debug(
      { crawlId, attempt, status: statusData.status },
      "Firecrawl crawl still in progress"
    );
  }

  throw new Error(
    `Firecrawl crawl timed out after ${(MAX_POLL_ATTEMPTS * POLL_INTERVAL_MS) / 1000}s. ` +
      `Crawl ID: ${crawlId} — you can check status manually.`
  );
}

/* ─── Method definition ───────────────────────────────────────────────── */

export function createGetStructuredInfo(
  domain: Domain
): MethodDefinition<typeof getStructuredInfoInputSchema, GetStructuredInfoOutput> {
  return {
    domain,
    name: "firecrawl.get_structured_info",
    description:
      "Scrape or crawl a webpage and extract structured data as JSON using a custom schema. " +
      "Use this tool when you know the specific URL of a website and need to extract " +
      "particular information in a well-defined, structured format. " +
      "\n\n" +
      "Two modes are available:\n" +
      "  • 'scrape' (default) — single-page extraction with stealth proxy. Fast, reliable, " +
      "works on sites with anti-bot protection (G2, Capterra, etc.). Use for one specific page.\n" +
      "  • 'crawl' — multi-page extraction that follows links up to a page limit. " +
      "Use when data spans multiple pages (paginated lists, multi-page docs). " +
      "May not work on heavily-protected sites.\n" +
      "\n" +
      "Common use-cases:\n" +
      "  • Extract pricing tiers and plans from a SaaS pricing page (scrape)\n" +
      "  • Extract review data from G2, Capterra, etc. (scrape)\n" +
      "  • Extract team member profiles, names, roles, and contact details (scrape)\n" +
      "  • Extract product feature comparisons or specification tables (scrape)\n" +
      "  • Gather data from multi-page documentation or blog archives (crawl)\n" +
      "  • Extract job listings across paginated results (crawl)\n" +
      "\n" +
      "You MUST provide three things:\n" +
      "  1. The target URL\n" +
      "  2. A JSON Schema object defining the exact shape of the data you want returned " +
      "(see the 'schema' parameter description for full examples)\n" +
      "  3. A natural-language prompt describing what to extract",
    inputSchema: getStructuredInfoInputSchema,

    async execute(input, _context) {
      if (input.mode === "scrape") {
        return executeScrape(input);
      }
      return executeCrawl(input);
    },
  };
}

export const getStructuredInfo = createGetStructuredInfo("crawler");
