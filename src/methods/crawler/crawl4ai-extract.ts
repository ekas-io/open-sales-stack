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

/* ─── Helpers ─────────────────────────────────────────────────────────── */

function buildRequestBody(
  input: ExtractInput,
  inputFormat: "markdown" | "html",
): Record<string, unknown> {
  return {
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
            input_format: inputFormat,
          },
        },
        ...(input.mode === "crawl" && {
          deep_crawl_strategy: {
            type: "BFSDeepCrawlStrategy",
            params: {
              max_depth: 2,
              max_pages: input.limit,
              include_external: false,
            },
          },
        }),
      },
    },
  };
}

function parseResults(
  results: Crawl4aiResult[],
  mode: "scrape" | "crawl",
): unknown {
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
  return mode === "scrape" && extractedData.length === 1
    ? extractedData[0]
    : extractedData;
}

/** Returns true if the extraction yielded usable data. */
function hasData(data: unknown): boolean {
  if (data == null) return false;
  if (Array.isArray(data) && data.length === 0) return false;
  if (typeof data === "object" && Object.keys(data as object).length === 0) return false;
  return true;
}

async function callCrawl4ai(
  input: ExtractInput,
  inputFormat: "markdown" | "html",
): Promise<{ data: unknown; results: Crawl4aiResult[] }> {
  const baseUrl = env.CRAWL4AI_BASE_URL;
  const requestBody = buildRequestBody(input, inputFormat);

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

  const results =
    crawlData.results ?? (crawlData.result ? [crawlData.result] : []);

  if (results.length === 0) {
    throw new Error("crawl4ai returned no results for the given URL");
  }

  const failed = results.filter((r) => !r.success);
  if (failed.length > 0 && failed.length === results.length) {
    throw new Error(
      `crawl4ai extraction failed: ${failed[0]?.error_message ?? "unknown error"}`
    );
  }

  return { data: parseResults(results, input.mode), results };
}

/* ─── Public API ──────────────────────────────────────────────────────── */

export async function crawl4aiExtract(input: ExtractInput): Promise<ExtractOutput> {
  logger.info(
    { url: input.url, mode: input.mode },
    "Starting crawl4ai extraction (markdown)"
  );

  // Try markdown first — it's cheaper on LLM tokens
  const markdownResult = await callCrawl4ai(input, "markdown");

  if (hasData(markdownResult.data)) {
    logger.info(
      { url: input.url, inputFormat: "markdown" },
      "crawl4ai extraction completed"
    );
    return {
      data: markdownResult.data,
      status: "completed",
      timestamp: new Date().toISOString(),
    };
  }

  // Markdown conversion sometimes produces near-empty output for JS-heavy
  // SPAs (e.g. Ashby job pages). Fall back to sending raw HTML to the LLM.
  logger.info(
    { url: input.url },
    "Markdown extraction returned empty data, retrying with html input_format"
  );

  const htmlResult = await callCrawl4ai(input, "html");

  logger.info(
    { url: input.url, inputFormat: "html", hasData: hasData(htmlResult.data) },
    "crawl4ai extraction completed (html fallback)"
  );

  return {
    data: htmlResult.data,
    status: "completed",
    timestamp: new Date().toISOString(),
  };
}
