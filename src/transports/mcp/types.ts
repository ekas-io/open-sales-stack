import type { ZodTypeAny } from "zod";
import type { MethodContext } from "../../methods/types";

export interface McpToolDefinition {
  /** Tool name exposed to MCP clients — must match the method ID (`domain.name`). */
  name: string;
  description: string;
  inputSchema: ZodTypeAny;
  execute: (args: unknown, context: MethodContext) => Promise<unknown>;
}
