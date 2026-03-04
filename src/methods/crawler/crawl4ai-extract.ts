import { env } from "../../config/env";
import { logger } from "../../lib/logger";
import type { ExtractInput, ExtractOutput } from "./firecrawl-extract";

/* ─── Response types ──────────────────────────────────────────────────── */

type Crawl4aiResult = {
  success: boolean;
  extracted_content?: string | null;
  url?: string;
  error_message?: string;
};

type Crawl4aiResponse = {
  success: boolean;
  results?: Crawl4aiResult[];
  result?: Crawl4aiResult;
};

/* ─── Public API ──────────────────────────────────────────────────────── */

export async function crawl4aiExtract(input: ExtractInput): Promise<ExtractOutput> {
  const baseUrl = env.CRAWL4AI_BASE_URL;

  // Build the request body for crawl4ai v0.8.0 /crawl endpoint.
  // v0.8.0 uses a `crawler_config` object with CrawlerRunConfig serialization,
  // NOT the legacy `extraction_config` format. `urls` must be an array.
  const requestBody: Record<string, unknown> = {
    urls: [input.url],
    crawler_config: {
      type: "CrawlerRunConfig",
      params: {
        extraction_strategy: {
          type: "LLMExtractionStrategy",
          params: {
            llm_config: {
              type: "LLMConfig",
              params: {
                provider: "openai/gpt-4o-mini",
                api_token: env.OPENAI_API_KEY,
              },
            },
            instruction: input.prompt,
            schema: input.schema,
            input_format: "markdown",
          },
        },
        ...(input.mode === "crawl" && { max_pages: input.limit }),
      },
    },
  };

  logger.info(
    { url: input.url, mode: input.mode },
    "Starting crawl4ai extraction"
  );

  // v0.8.0 returns results synchronously — no task_id polling needed
  const crawlResponse = await fetch(`${baseUrl}/crawl`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(requestBody),
  });

  if (!crawlResponse.ok) {
    const errorText = await crawlResponse.text();
    throw new Error(
      `crawl4ai API error (${crawlResponse.status}): ${errorText}`
    );
  }

  const crawlData = (await crawlResponse.json()) as Crawl4aiResponse;

  // Handle both single-result and multi-result responses
  const results =
    crawlData.results ?? (crawlData.result ? [crawlData.result] : []);

  if (results.length === 0) {
    throw new Error("crawl4ai returned no results for the given URL");
  }

  // Check for failures
  const failed = results.filter((r) => !r.success);
  if (failed.length > 0 && failed.length === results.length) {
    throw new Error(
      `crawl4ai extraction failed: ${failed[0]?.error_message ?? "unknown error"}`
    );
  }

  // Parse extracted_content from each result.
  // extracted_content is a JSON string that typically contains an array.
  const extractedData = results
    .filter((r) => r.success && r.extracted_content)
    .map((r) => {
      let parsed: unknown = r.extracted_content;
      if (typeof parsed === "string") {
        try {
          parsed = JSON.parse(parsed);
        } catch {
          logger.warn(
            { url: r.url },
            "Could not parse extracted_content as JSON, returning raw string"
          );
        }
      }
      // extracted_content often parses to an array with a single object;
      // unwrap it for convenience
      if (Array.isArray(parsed) && parsed.length === 1) {
        parsed = parsed[0];
      }
      return parsed;
    });

  // For single-page scrape, return the first result directly.
  // For multi-page crawl, return the full array.
  const data =
    input.mode === "scrape" && extractedData.length === 1
      ? extractedData[0]
      : extractedData;

  logger.info(
    { url: input.url, resultCount: extractedData.length },
    "crawl4ai extraction completed"
  );

  return {
    data,
    status: "completed",
    timestamp: new Date().toISOString(),
  };
}
