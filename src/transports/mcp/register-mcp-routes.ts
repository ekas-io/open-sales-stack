import { randomUUID } from "node:crypto";
import type { Express, Request, Response } from "express";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { isInitializeRequest } from "@modelcontextprotocol/sdk/types.js";
import { logger } from "../../lib/logger";
import { apiKeyAuth } from "../../middleware/api-key-auth";
import { createMcpServer } from "./create-mcp-server";

/** Active transports keyed by session ID. */
const transports: Record<string, StreamableHTTPServerTransport> = {};

/**
 * Registers MCP Streamable HTTP endpoints on the Express app.
 *
 * All three verbs share a single `/mcp` path:
 *   POST   /mcp  — JSON-RPC messages (including initialization)
 *   GET    /mcp  — SSE stream for server→client notifications
 *   DELETE /mcp  — session termination
 *
 * Auth uses the same `x-api-key` header as the REST API.
 */
export function registerMcpRoutes(app: Express): void {
  // ── POST: JSON-RPC messages ─────────────────────────────────────────
  app.post("/mcp", apiKeyAuth, async (req: Request, res: Response) => {
    const sessionId = req.headers["mcp-session-id"] as string | undefined;

    try {
      if (sessionId && transports[sessionId]) {
        // Existing session — forward to its transport
        await transports[sessionId].handleRequest(req, res, req.body);
        return;
      }

      if (!sessionId && isInitializeRequest(req.body)) {
        // New session — create transport + server
        const transport = new StreamableHTTPServerTransport({
          sessionIdGenerator: () => randomUUID(),
          onsessioninitialized: (sid) => {
            logger.info({ sessionId: sid }, "MCP session initialized");
            transports[sid] = transport;
          },
        });

        transport.onclose = () => {
          const sid = transport.sessionId;
          if (sid && transports[sid]) {
            logger.info({ sessionId: sid }, "MCP session closed");
            delete transports[sid];
          }
        };

        const server = createMcpServer();
        await server.connect(transport);
        await transport.handleRequest(req, res, req.body);
        return;
      }

      // Invalid — neither a known session nor a valid init request
      res.status(400).json({
        jsonrpc: "2.0",
        error: {
          code: -32000,
          message: "Bad Request: no valid session ID provided",
        },
        id: null,
      });
    } catch (error) {
      logger.error({ err: error }, "Error handling MCP POST");
      if (!res.headersSent) {
        res.status(500).json({
          jsonrpc: "2.0",
          error: { code: -32603, message: "Internal server error" },
          id: null,
        });
      }
    }
  });

  // ── GET: SSE stream for server-initiated messages ───────────────────
  app.get("/mcp", apiKeyAuth, async (req: Request, res: Response) => {
    const sessionId = req.headers["mcp-session-id"] as string | undefined;

    if (!sessionId || !transports[sessionId]) {
      res.status(400).json({
        error: { code: "INVALID_SESSION", message: "Invalid or missing session ID" },
      });
      return;
    }

    await transports[sessionId].handleRequest(req, res);
  });

  // ── DELETE: session termination ─────────────────────────────────────
  app.delete("/mcp", apiKeyAuth, async (req: Request, res: Response) => {
    const sessionId = req.headers["mcp-session-id"] as string | undefined;

    if (!sessionId || !transports[sessionId]) {
      res.status(400).json({
        error: { code: "INVALID_SESSION", message: "Invalid or missing session ID" },
      });
      return;
    }

    try {
      await transports[sessionId].handleRequest(req, res);
    } catch (error) {
      logger.error({ err: error }, "Error handling MCP session termination");
      if (!res.headersSent) {
        res.status(500).json({ error: { message: "Error processing session termination" } });
      }
    }
  });
}
