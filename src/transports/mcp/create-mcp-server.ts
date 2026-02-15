import crypto from "node:crypto";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import type { ZodObject, ZodRawShape } from "zod";
import { mcpTools } from "./tools/index";

/**
 * Creates a fresh McpServer instance with all registered tools.
 *
 * A new server is created per session so each client gets an
 * independent context. Tool dispatch is handled internally by
 * the SDK via a Map keyed on tool name — no manual if/else chain.
 */
export function createMcpServer(): McpServer {
  const server = new McpServer({
    name: "ekas-mcps",
    version: "0.1.0",
  });

  for (const tool of mcpTools) {
    // Extract the raw Zod shape from the ZodObject so the SDK can
    // convert it to JSON Schema for the tools/list response.
    const shape = (tool.inputSchema as ZodObject<ZodRawShape>).shape;

    server.registerTool(tool.name, {
      description: tool.description,
      inputSchema: shape,
    }, async (args) => {
      const result = await tool.execute(args, {
        requestId: crypto.randomUUID(),
      });

      return {
        content: [
          {
            type: "text" as const,
            text: JSON.stringify(result),
          },
        ],
      };
    });
  }

  return server;
}
