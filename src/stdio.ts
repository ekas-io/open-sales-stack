import "dotenv/config";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { createMcpServer } from "./transports/mcp/create-mcp-server";

const server = createMcpServer();
const transport = new StdioServerTransport();
await server.connect(transport);
