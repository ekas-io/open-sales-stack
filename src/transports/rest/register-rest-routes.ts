import crypto from "node:crypto";
import type { Express, Request, Response } from "express";
import { HttpError } from "../../lib/http-error";
import { methodList, methodRegistry } from "../../methods/index";
import { apiKeyAuth } from "../../middleware/api-key-auth";

function getRequestId(req: Request): string {
  const headerId = req.header("x-request-id");
  return headerId || crypto.randomUUID();
}

export function registerRestRoutes(app: Express): void {
  app.use("/api", apiKeyAuth);

  app.get("/api/methods", (_req: Request, res: Response) => {
    res.json({
      methods: methodList.map((method) => ({
        id: method.id,
        domain: method.domain,
        name: method.name,
        description: method.description
      }))
    });
  });

  app.post("/api/:domain/:method", async (req: Request, res: Response, next) => {
    try {
      const key = `${req.params.domain}.${req.params.method}`;
      const method = methodRegistry.get(key);

      if (!method) {
        throw new HttpError(404, `Method not found: ${key}`);
      }

      const parsedInput = method.inputSchema.safeParse(req.body ?? {});
      if (!parsedInput.success) {
        throw new HttpError(400, "Invalid request body", parsedInput.error.format());
      }

      const output = await method.execute(parsedInput.data, {
        requestId: getRequestId(req)
      });

      res.status(200).json({
        method: method.id,
        data: output
      });
    } catch (error) {
      next(error);
    }
  });
}
