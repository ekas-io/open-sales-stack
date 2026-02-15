import { z } from "zod";
import { env } from "../../config/env";
import type { Domain, MethodDefinition } from "../types";
import { logger } from "../../lib/logger";

/**
 * Input schema for the structured-info crawler.
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
      "The full URL of the webpage to crawl and extract structured data from. " +
        "Must be a valid, publicly accessible URL including the protocol " +
        "(e.g. 'https://example.com/pricing'). This is the starting page — " +
        "the crawler may follow links within the same domain up to the " +
        "specified limit."
    ),

  schema: z
    .record(z.any())
    .describe(
      "A valid JSON Schema object that defines the exact structure of the data you want extracted. " +
        "The crawler uses this schema so the returned JSON matches your specification exactly. " +
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
      "A clear, natural-language instruction telling the crawler exactly what information " +
        "to extract from the page(s). Be as specific as possible about the data points you need. " +
        "Good examples:\n" +
        "  • 'Extract all pricing tiers including tier name, monthly price, annual price, and included features'\n" +
        "  • 'Find all team members with their names, job titles, and LinkedIn URLs'\n" +
        "  • 'Extract product announcements including title, date, and summary from the changelog'\n" +
        "  • 'Get all contact information: office addresses, phone numbers, and support emails'"
    ),

  limit: z
    .number()
    .int()
    .positive()
    .max(10)
    .default(5)
    .describe(
      "Maximum number of pages to crawl starting from the given URL. Defaults to 5, max is 10. " +
        "Set to 1 if you only need data from the exact URL provided. Increase if the " +
        "information might span multiple pages (e.g. paginated lists, multi-page docs). " +
        "Higher values increase crawl time."
    ),
});

type GetStructuredInfoOutput = {
  data: unknown;
  status: string;
  crawlId: string;
  totalPages: number;
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

export function createGetStructuredInfo(
  domain: Domain
): MethodDefinition<typeof getStructuredInfoInputSchema, GetStructuredInfoOutput> {
  return {
    domain,
    name: "firecrawl.get_structured_info",
    description:
      "Crawl a webpage and extract structured data as JSON using a custom schema. " +
      "Use this tool when you know the specific URL of a website and need to extract " +
      "particular information in a well-defined, structured format. " +
      "\n\n" +
      "Common use-cases:\n" +
      "  • Extract pricing tiers and plans from a SaaS pricing page\n" +
      "  • Extract team member profiles, names, roles, and contact details\n" +
      "  • Extract product feature comparisons or specification tables\n" +
      "  • Extract changelog entries, release notes, or product announcements\n" +
      "  • Extract job listings with titles, locations, and requirements\n" +
      "  • Extract contact information (addresses, phone numbers, emails)\n" +
      "  • Extract any other structured data visible on public web pages\n" +
      "\n" +
      "You MUST provide three things:\n" +
      "  1. The target URL to crawl\n" +
      "  2. A JSON Schema object defining the exact shape of the data you want returned " +
      "(see the 'schema' parameter description for full examples)\n" +
      "  3. A natural-language prompt describing what to extract\n" +
      "\n" +
      "The crawler visits the URL (and optionally follows links up to the page limit), " +
      "then uses AI to extract data matching your schema and returns it as structured JSON.",
    inputSchema: getStructuredInfoInputSchema,

    async execute(input, _context) {
      // ── 1. Start the crawl ────────────────────────────────────────────
      const crawlBody = {
        url: input.url,
        sitemap: "include",
        crawlEntireDomain: false,
        limit: input.limit,
        scrapeOptions: {
          onlyMainContent: false,
          maxAge: 172_800_000, // 48 hours cache
          parsers: ["pdf"],
          formats: [
            {
              type: "json",
              schema: input.schema,
              prompt: input.prompt,
            },
          ],
        },
      };

      logger.info(
        { url: input.url, limit: input.limit },
        "Starting Firecrawl structured crawl"
      );

      const crawlResponse = await fetch(`${FIRECRAWL_BASE_URL}/crawl`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${env.FIRECRAWL_API_KEY}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(crawlBody),
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

      // ── 2. Poll until complete ────────────────────────────────────────
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
    },
  };
}

export const getStructuredInfo = createGetStructuredInfo("crawler");
