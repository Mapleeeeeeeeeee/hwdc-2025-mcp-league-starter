import { z } from "zod";

/**
 * Frontend Configuration Module
 *
 * Centralized configuration management for environment variables and app settings.
 * Provides type-safe access to configuration values with defaults and validation.
 *
 * Note: Only NEXT_PUBLIC_ prefixed environment variables are accessible in client components.
 * Server-only variables should be handled separately in server components or API routes.
 *
 * API Routing Strategy:
 * - Development: Next.js rewrites proxy /api/* to backend (configured in next.config.ts)
 * - Production: Nginx reverse proxy handles /api/* routing
 * - API client always uses relative paths (e.g., /api/users)
 */

const ENVIRONMENTS = ["development", "production", "test", "staging"] as const;

const environmentSchema = z.enum(ENVIRONMENTS);

// Schema for application configuration
const appConfigSchema = z.object({
  /** Application environment resolved from env variables */
  appEnv: environmentSchema,
  /** Node environment reported by the runtime */
  nodeEnv: environmentSchema,
  /** Whether the app is running in development mode */
  isDevelopment: z.boolean(),
  /** Whether the app is running in production mode */
  isProduction: z.boolean(),
});

type AppConfig = z.infer<typeof appConfigSchema>;

/**
 * Raw environment variables (only NEXT_PUBLIC_ prefixed for client safety)
 */
const rawEnv = {
  appEnv: process.env.NEXT_PUBLIC_APP_ENV,
  nodeEnv: process.env.NODE_ENV,
};

/**
 * Parse and validate configuration
 * Throws ZodError if required environment variables are missing or invalid
 */
function createConfig(): AppConfig {
  // Resolve environment with priority: NEXT_PUBLIC_APP_ENV > NODE_ENV
  const resolvedAppEnv = environmentSchema.parse(
    rawEnv.appEnv ?? rawEnv.nodeEnv,
  );

  const resolvedNodeEnv = environmentSchema.parse(rawEnv.nodeEnv);

  return appConfigSchema.parse({
    appEnv: resolvedAppEnv,
    nodeEnv: resolvedNodeEnv,
    isDevelopment: resolvedAppEnv !== "production",
    isProduction: resolvedAppEnv === "production",
  });
}

/**
 * Application configuration object
 * All environment variables are accessed through this centralized config
 */
export const config = createConfig();

export default config;
