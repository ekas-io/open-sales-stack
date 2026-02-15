import { z } from "zod";
import { env } from "../../../../config/env";
import type { Domain, MethodDefinition } from "../../../types";

const peopleDetailsInputSchema = z.object({
  linkedin_url: z.string().url().min(1, "linkedin_url is required")
});

type PeopleDetailsOutput = {
  results: unknown[];
  total: number;
  timestamp: string;
};

export function createPeopleDetails(
  domain: Domain
): MethodDefinition<typeof peopleDetailsInputSchema, PeopleDetailsOutput> {
  return {
    domain,
    name: "coresignal.people.get_details",
    description: "Get all possible details about an employee from LinkedIn using. Use this tool when your running a prospect research and need to learn more about the person, like their company, title, location, linkedin posts, experience, details about their current company etc.",
    inputSchema: peopleDetailsInputSchema,
    async execute(input, _context) {
      const url = "https://api.coresignal.com/cdapi/v2/employee_multi_source/search/es_dsl";
      
      const requestBody = {
        query: {
          bool: {
            must: [
              {
                match_phrase: {
                  linkedin_url: input.linkedin_url
                }
              }
            ]
          }
        }
      };

      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "apikey": env.CORESIGNAL_API_KEY
        },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(
          `Coresignal API error (${response.status}): ${errorText}`
        );
      }

      const data = await response.json();

      return {
        results: data.hits?.hits || [],
        total: data.hits?.total?.value || 0,
        timestamp: new Date().toISOString()
      };
    }
  };
}

export const getPeopleDetails = createPeopleDetails("data");
