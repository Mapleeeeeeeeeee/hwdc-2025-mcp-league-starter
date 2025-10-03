import { z } from "zod";

/**
 * Frontend Configuration Module
 *
 * Centralized configuration management for environment variables and app settings.
 * Provides type-safe access to configuration values with defaults and validation.
 *
 * Note: Only NEXT_PUBLIC_ prefixed environment variables are accessible in client components.
 * Server-only variables should be handled separately in server components or API routes.
 */

const ENVIRONMENTS = ["development", "production", "test", "staging"] as const;

const environmentSchema = z.enum(ENVIRONMENTS);

// Schema for client-side accessible configuration
const clientConfigSchema = z.object({
  /** API base URL for backend communication */
  apiBaseUrl: z.string().url().default("http://localhost:8080"),
  /** Application environment resolved from env variables */
  environment: environmentSchema.default("development"),
});

// Schema for derived configuration values
const derivedConfigSchema = z.object({
  /** Application environment resolved from env variables */
  appEnv: environmentSchema,
  /** Node environment reported by the runtime */
  nodeEnv: environmentSchema,
  /** Whether the app is running in development mode */
  isDevelopment: z.boolean(),
  /** Whether the app is running in production mode */
  isProduction: z.boolean(),
});

// Combined configuration schema
const appConfigSchema = clientConfigSchema.merge(derivedConfigSchema);

type AppConfig = z.infer<typeof appConfigSchema>;

/**
 * Raw environment variables (only NEXT_PUBLIC_ prefixed for client safety)
 */
const rawEnv = {
  apiBaseUrl: process.env.NEXT_PUBLIC_API_BASE_URL,
  appEnv: process.env.NEXT_PUBLIC_APP_ENV,
  nodeEnv: process.env.NODE_ENV,
};

/**
 * Parse and validate configuration
 */
function createConfig(): AppConfig {
  const fallbackEnvironment: (typeof ENVIRONMENTS)[number] = "development";

  const resolvedAppEnvResult = environmentSchema.safeParse(
    rawEnv.appEnv ?? rawEnv.nodeEnv,
  );
  const resolvedAppEnv = resolvedAppEnvResult.success
    ? resolvedAppEnvResult.data
    : fallbackEnvironment;

  const resolvedNodeEnvResult = environmentSchema.safeParse(rawEnv.nodeEnv);
  const resolvedNodeEnv = resolvedNodeEnvResult.success
    ? resolvedNodeEnvResult.data
    : fallbackEnvironment;

  // Parse client config with defaults
  const clientConfig = clientConfigSchema.parse({
    apiBaseUrl: rawEnv.apiBaseUrl,
    environment: resolvedAppEnv,
  });

  // Create derived config prioritising APP_ENV
  const derivedConfig = {
    appEnv: resolvedAppEnv,
    nodeEnv: resolvedNodeEnv,
    isDevelopment: resolvedAppEnv !== "production",
    isProduction: resolvedAppEnv === "production",
  } as const;

  // Combine and validate final config
  return appConfigSchema.parse({
    ...clientConfig,
    ...derivedConfig,
  });
}

/**
 * Application configuration object
 * All environment variables are accessed through this centralized config
 */
export const config = createConfig();

export default config;
