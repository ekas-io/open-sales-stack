import { z } from "zod";
import type { Domain, MethodDefinition } from "../types";
import { crawl4aiExtract } from "./crawl4ai-extract";
import type { ExtractOutput } from "./firecrawl-extract";

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
        "Uses a headless browser with full JavaScript rendering. " +
        "Best for: extracting data from one specific page — " +
        "reviews, pricing, a company profile, etc.\n\n" +
        "• 'crawl' — Starts from the given URL and follows links within the " +
        "same domain, scraping up to 'limit' pages. " +
        "Best for: gathering data spread " +
        "across multiple pages — paginated review lists, multi-page docs, " +
        "sitemaps, blog archives."
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

/* ─── Method definition ───────────────────────────────────────────────── */

export function createGetStructuredInfo(
  domain: Domain
): MethodDefinition<typeof getStructuredInfoInputSchema, ExtractOutput> {
  return {
    domain,
    name: "get_structured_info",
    description:
      "Scrape or crawl a webpage and extract structured data as JSON using a custom schema. " +
      "Use this tool when you know the specific URL of a website and need to extract " +
      "particular information in a well-defined, structured format. " +
      "\n\n" +
      "Two modes are available:\n" +
      "  • 'scrape' (default) — single-page extraction with full JS rendering. Fast, reliable, " +
      "handles JavaScript-heavy SPAs and sites that require browser rendering.\n" +
      "  • 'crawl' — multi-page extraction that follows links up to a page limit. " +
      "Use when data spans multiple pages (paginated lists, multi-page docs).\n" +
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
      return crawl4aiExtract(input);
    },
  };
}

export const getStructuredInfo = createGetStructuredInfo("crawler");
