import { z } from "zod";
import { env } from "../../../../config/env";
import type { Domain, MethodDefinition } from "../../../types";
import { logger } from "../../../../lib/logger";

const CORESIGNAL_BASE_URL =
  "https://api.coresignal.com/cdapi/v2/employee_multi_source";

const peopleDetailsInputSchema = z.object({
  linkedin_url: z
    .string()
    .url()
    .min(1, "linkedin_url is required")
    .describe(
      "The full LinkedIn profile URL of the person to look up " +
        "(e.g. 'https://www.linkedin.com/in/john-doe-123456')."
    ),
});

type PeopleDetailsOutput = {
  data: unknown;
  timestamp: string;
};

function coresignalHeaders(): Record<string, string> {
  return {
    "Content-Type": "application/json",
    apikey: env.CORESIGNAL_API_KEY,
  };
}

export function createPeopleDetails(
  domain: Domain
): MethodDefinition<typeof peopleDetailsInputSchema, PeopleDetailsOutput> {
  return {
    domain,
    name: "coresignal.people.get_details",
    description:
      "Get all possible details about an employee from LinkedIn. Use this tool when " +
      "you're running prospect research and need to learn more about a person — their " +
      "company, title, location, LinkedIn posts, experience, skills, details about " +
      "their current company, etc.",
    inputSchema: peopleDetailsInputSchema,

    async execute(input, _context) {
      // ── 1. Search: LinkedIn URL → employee ID(s) ───────────────────
      const searchBody = {
        query: {
          bool: {
            must: [
              { match_phrase: { linkedin_url: input.linkedin_url } },
            ],
          },
        },
      };

      logger.info(
        { linkedin_url: input.linkedin_url },
        "Coresignal people search"
      );

      const searchResponse = await fetch(`${CORESIGNAL_BASE_URL}/search/es_dsl`, {
        method: "POST",
        headers: coresignalHeaders(),
        body: JSON.stringify(searchBody),
      });

      if (!searchResponse.ok) {
        const errorText = await searchResponse.text();
        throw new Error(
          `Coresignal search error (${searchResponse.status}): ${errorText}`
        );
      }

      const ids = (await searchResponse.json()) as number[];

      if (!Array.isArray(ids) || ids.length === 0) {
        throw new Error(
          `No Coresignal results found for LinkedIn URL: ${input.linkedin_url}`
        );
      }

      // ── 2. Collect: employee ID → full profile ─────────────────────
      const employeeId = ids[0];

      logger.info(
        { employeeId, linkedin_url: input.linkedin_url },
        "Coresignal people collect"
      );

      const collectResponse = await fetch(
        `${CORESIGNAL_BASE_URL}/collect/${employeeId}`,
        {
          method: "GET",
          headers: coresignalHeaders(),
        }
      );

      if (!collectResponse.ok) {
        const errorText = await collectResponse.text();
        throw new Error(
          `Coresignal collect error (${collectResponse.status}): ${errorText}`
        );
      }

      const profile = await collectResponse.json();

      logger.info(
        { employeeId, name: profile.full_name },
        "Coresignal people collect completed"
      );

      return {
        data: profile,
        timestamp: new Date().toISOString(),
      };
    },
  };
}

export const getPeopleDetails = createPeopleDetails("data");
