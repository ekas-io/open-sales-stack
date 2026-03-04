import { env } from "../../config/env";
import { logger } from "../../lib/logger";

/* ─── Types ───────────────────────────────────────────────────────────── */

export type ExtractInput = {
  url: string;
  schema: Record<string, unknown>;
  prompt: string;
  mode: "scrape" | "crawl";
  limit: number;
};

export type ExtractOutput = {
  data: unknown;
  status: string;
  metadata?: unknown;
  crawlId?: string;
  totalPages?: number;
  timestamp: string;
};

/* ─── Constants ────────────────────────────────────────────────────────── */

const FIRECRAWL_BASE_URL = "https://api.firecrawl.dev/v2";
const POLL_INTERVAL_MS = 5_000;
const MAX_POLL_ATTEMPTS = 120; // 10 minutes max

/* ─── Helpers ──────────────────────────────────────────────────────────── */

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

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

async function callScrape(
  input: ExtractInput,
  proxy: "basic" | "stealth",
): Promise<ScrapeResult> {
  const body: Record<string, unknown> = {
    url: input.url,
    timeout: 120_000,
    formats: [jsonFormat(input.schema, input.prompt)],
    proxy,
  };

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

async function executeScrape(input: ExtractInput): Promise<ExtractOutput> {
  logger.info(
    { url: input.url, mode: "scrape", proxy: "basic" },
    "Starting Firecrawl scrape (basic proxy)"
  );

  const basicResult = await callScrape(input, "basic");

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

  logger.info(
    { url: input.url, basicError: basicResult.error ?? basicResult.code ?? "empty json" },
    "Basic proxy returned no data, retrying with stealth proxy"
  );

  const stealthResult = await callScrape(input, "stealth");

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

  throw new Error(
    `Firecrawl scrape failed (both basic and stealth): ${stealthResult.error ?? basicResult.error ?? JSON.stringify(stealthResult)}`
  );
}

/* ─── Crawl (multi-page, async polling) ───────────────────────────────── */

async function executeCrawl(input: ExtractInput): Promise<ExtractOutput> {
  const body = {
    url: input.url,
    sitemap: "include",
    crawlEntireDomain: false,
    limit: input.limit,
    scrapeOptions: {
      onlyMainContent: false,
      maxAge: 172_800_000,
      parsers: ["pdf"],
      formats: [jsonFormat(input.schema, input.prompt)],
    },
  };

  logger.info(
    { url: input.url, limit: input.limit, mode: "crawl" },
    "Starting Firecrawl crawl"
  );

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

/* ─── Public API ──────────────────────────────────────────────────────── */

export async function firecrawlExtract(input: ExtractInput): Promise<ExtractOutput> {
  if (input.mode === "scrape") {
    return executeScrape(input);
  }
  return executeCrawl(input);
}
