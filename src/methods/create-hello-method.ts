import { z } from "zod";
import type { Domain, MethodDefinition } from "./types";

const helloInputSchema = z
  .object({
    name: z.string().min(1).max(120).optional()
  })
  .default({});

export function createHelloMethod(
  domain: Domain
): MethodDefinition<typeof helloInputSchema, Record<string, string>> {
  return {
    domain,
    name: "hello",
    description: `Hello world method for the ${domain} domain`,
    inputSchema: helloInputSchema,
    async execute(input, _context) {
      const target = input.name?.trim() || "world";
      const timestamp = new Date().toISOString();

      return {
        domain,
        message: `Hello ${target} from ${domain}`,
        timestamp
      };
    }
  };
}
