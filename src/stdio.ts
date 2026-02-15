/**
 * Stdio entry point for MCP clients that use stdio transport
 * (e.g. Claude Desktop, Cursor).
 *
 * Usage in Claude Desktop config:
 *   "command": "npx",
 *   "args": ["tsx", "<absolute-path>/src/stdio.ts"],
 *   "env": { "DOTENV_CONFIG_PATH": "<absolute-path>/.env" }
 */
import "dotenv/config";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { createMcpServer } from "./transports/mcp/create-mcp-server";

async function main() {
  const server = createMcpServer();
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
