import type { NextFunction, Request, Response } from "express";
import { env } from "../config/env";

export function apiKeyAuth(req: Request, res: Response, next: NextFunction): void {
  const apiKey = req.header("x-api-key");

  if (apiKey !== env.API_KEY) {
    res.status(401).json({
      error: {
        code: "UNAUTHORIZED",
        message: "Missing or invalid API key"
      }
    });
    return;
  }

  next();
}
