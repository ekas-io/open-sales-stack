import type { z, ZodTypeAny } from "zod";

export type Domain = "data" | "crawler" | "crm";

export interface MethodContext {
  requestId: string;
}

export interface MethodDefinition<
  TInputSchema extends ZodTypeAny,
  TOutput = unknown
> {
  domain: Domain;
  name: string;
  description: string;
  inputSchema: TInputSchema;
  execute: (input: z.infer<TInputSchema>, context: MethodContext) => Promise<TOutput>;
}

export type AnyMethod = MethodDefinition<ZodTypeAny, unknown>;

export interface RegisteredMethod {
  id: string;
  domain: Domain;
  name: string;
  description: string;
  inputSchema: ZodTypeAny;
  execute: (input: unknown, context: MethodContext) => Promise<unknown>;
}
