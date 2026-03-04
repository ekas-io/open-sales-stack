import { z } from "zod";

const envSchema = z.object({
  NODE_ENV: z.enum(["development", "test", "production"]).default("development"),
  PORT: z.coerce.number().int().positive().default(8080),
  LOG_LEVEL: z
    .enum(["fatal", "error", "warn", "info", "debug", "trace", "silent"])
    .default("info"),
  API_KEY: z
    .string()
    .min(32, "API_KEY must be at least 32 characters. Use a strong random key."),
  CORS_ORIGIN: z.string().optional(),
  CORESIGNAL_API_KEY: z.string().min(1, "CORESIGNAL_API_KEY is required"),
  FIRECRAWL_API_KEY: z.string().min(1, "FIRECRAWL_API_KEY is required"),
  CHROME_CDP_URL: z
    .string()
    .url()
    .default("http://localhost:9222")
    .describe("Chrome DevTools Protocol endpoint for Playwright to connect to"),
  CRAWL4AI_BASE_URL: z
    .string()
    .url()
    .default("http://localhost:11235")
    .describe("Base URL for the self-hosted crawl4ai Docker service"),
  OPENAI_API_KEY: z
    .string()
    .min(1, "OPENAI_API_KEY is required for crawl4ai LLM extraction"),
});

const parsed = envSchema.safeParse(process.env);

if (!parsed.success) {
  const details = parsed.error.errors
    .map((issue) => `${issue.path.join(".")}: ${issue.message}`)
    .join("; ");

  throw new Error(`Invalid environment configuration: ${details}`);
}

export const env = parsed.data;
