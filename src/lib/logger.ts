import pino from "pino";
import { env } from "../config/env";

// When used as a stdio MCP transport, stdout is reserved for JSON-RPC.
// Route all logs to stderr (fd 2) so they never corrupt the protocol.
export const logger = pino({
  level: env.LOG_LEVEL,
  redact: {
    paths: ["req.headers.authorization", "req.headers.x-api-key"],
    remove: true,
  },
}, pino.destination(2));
