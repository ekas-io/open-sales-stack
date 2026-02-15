import type { ZodTypeAny } from "zod";
import type { MethodDefinition } from "../../methods/types";
import type { McpToolDefinition } from "./types";

/**
 * Convert a MethodDefinition to an McpToolDefinition.
 *
 * The MCP tool name is derived from `{domain}_{name}` with all dots
 * replaced by underscores to satisfy the MCP spec constraint:
 *   ^[a-zA-Z0-9_-]{1,64}$
 *
 * Usage:
 *   export const tool = fromMethod(myMethod);
 */
export function fromMethod<TSchema extends ZodTypeAny, TOutput>(
  method: MethodDefinition<TSchema, TOutput>
): McpToolDefinition {
  const name = `${method.domain}_${method.name}`.replaceAll(".", "_");

  return {
    name,
    description: method.description,
    inputSchema: method.inputSchema,
    execute: method.execute as McpToolDefinition["execute"],
  };
}
