import { z } from "zod";
import { env } from "../../../../config/env";
import type { Domain, MethodDefinition } from "../../../types";

const companyDetailsInputSchema = z.object({
  website: z.string().min(1, "website is required")
});

type CompanyDetailsOutput = {
  data: unknown;
  timestamp: string;
};

export function createCompanyDetails(
  domain: Domain
): MethodDefinition<typeof companyDetailsInputSchema, CompanyDetailsOutput> {
  return {
    domain,
    name: "coresignal.company.get_details",
    description: "Get a very thorough details about a company, like Firmographics Contact information Location Workforce Products Social media Web traffic Company reviews News features Competitive insights Financials Funding Workforce trends Company traction & changes Ownership and acquisitions Technographics. Use this tool when your running a prospect research and need to learn everything about the company",
    inputSchema: companyDetailsInputSchema,
    async execute(input, _context) {
      const url = new URL("https://api.coresignal.com/cdapi/v2/company_multi_source/enrich");
      url.searchParams.append("website", input.website);

      const response = await fetch(url.toString(), {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          "apikey": env.CORESIGNAL_API_KEY
        }
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(
          `Coresignal API error (${response.status}): ${errorText}`
        );
      }

      const data = await response.json();

      return {
        data,
        timestamp: new Date().toISOString()
      };
    }
  };
}

export const getCompanyDetails = createCompanyDetails("data");
