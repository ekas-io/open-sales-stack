import type { McpToolDefinition } from "../types";
import { tool as getCompanyDetails } from "./get-company-details";
import { tool as getPeopleDetails } from "./get-people-details";

/**
 * All MCP tools to expose.
 *
 * To add a new tool:
 *   1. Create a file in this folder:  export const tool = fromMethod(myMethod);
 *   2. Import and append it to the array below.
 *
 * The tool name is derived automatically from the method's domain + name,
 * so dispatch never needs a manual if/else chain.
 */
export const mcpTools: McpToolDefinition[] = [
  getPeopleDetails,
  getCompanyDetails,
];
