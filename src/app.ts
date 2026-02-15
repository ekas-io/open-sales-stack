import crypto from "node:crypto";
import cors from "cors";
import express, { type NextFunction, type Request, type Response } from "express";
import rateLimit from "express-rate-limit";
import helmet from "helmet";
import { pinoHttp } from "pino-http";
import { env } from "./config/env";
import { HttpError } from "./lib/http-error";
import { logger } from "./lib/logger";
import { registerMcpRoutes } from "./transports/mcp/register-mcp-routes";
import { registerRestRoutes } from "./transports/rest/register-rest-routes";

export function createApp() {
  const app = express();

  app.disable("x-powered-by");
  app.set("trust proxy", true);

  app.use(
    pinoHttp({
      logger,
      genReqId: (req: Request) => req.headers["x-request-id"]?.toString() || crypto.randomUUID()
    })
  );

  app.use(
    helmet({
      crossOriginResourcePolicy: { policy: "cross-origin" }
    })
  );

  if (env.CORS_ORIGIN) {
    app.use(
      cors({
        origin: env.CORS_ORIGIN,
        methods: ["POST", "GET", "DELETE", "OPTIONS"],
        allowedHeaders: ["content-type", "x-api-key", "authorization", "x-request-id", "mcp-session-id"]
      })
    );
  }

  app.use(
    express.json({
      strict: true,
      type: "application/json"
    })
  );

  app.use(
    rateLimit({
      windowMs: 60 * 1000,
      limit: 120,
      standardHeaders: true,
      legacyHeaders: false
    })
  );

  app.get("/health", (_req: Request, res: Response) => {
    res.status(200).json({ status: "ok" });
  });

  registerRestRoutes(app);
  registerMcpRoutes(app);

  // Return a plain 404 for OAuth/.well-known discovery so mcp-remote
  // doesn't choke on our JSON error format during OAuth probing.
  app.use("/.well-known", (_req: Request, res: Response) => {
    res.status(404).end();
  });

  app.use((_req: Request, res: Response) => {
    res.status(404).json({ error: { code: "NOT_FOUND", message: "Route not found" } });
  });

  app.use((error: unknown, _req: Request, res: Response, _next: NextFunction) => {
    if (error instanceof HttpError) {
      res.status(error.statusCode).json({
        error: {
          code: "REQUEST_ERROR",
          message: error.message,
          details: error.details
        }
      });
      return;
    }

    logger.error({ err: error }, "Unhandled error");
    res.status(500).json({
      error: {
        code: "INTERNAL_SERVER_ERROR",
        message: "Unexpected error"
      }
    });
  });

  return app;
}
