import { z } from "zod";

const ENVIRONMENTS = ["development", "production", "test", "staging"] as const;
const environmentSchema = z.enum(ENVIRONMENTS);

const appConfigSchema = z.object({
  appEnv: environmentSchema,
  nodeEnv: environmentSchema,
  isDevelopment: z.boolean(),
  isProduction: z.boolean(),
  apiTimeout: z.number().min(1000).max(300000),
  apiTimeoutLongRunning: z.number().min(1000).max(600000),
  apiTimeoutConversation: z.number().min(1000).max(600000),
});

type AppConfig = z.infer<typeof appConfigSchema>;

const rawEnv = {
  appEnv: process.env.NEXT_PUBLIC_APP_ENV,
  nodeEnv: process.env.NODE_ENV,
  apiTimeout: process.env.NEXT_PUBLIC_API_TIMEOUT,
  apiTimeoutLongRunning: process.env.NEXT_PUBLIC_API_TIMEOUT_LONG_RUNNING,
  apiTimeoutConversation: process.env.NEXT_PUBLIC_API_TIMEOUT_CONVERSATION,
};

function createConfig(): AppConfig {
  const resolvedAppEnv = environmentSchema.parse(
    rawEnv.appEnv ?? rawEnv.nodeEnv,
  );
  const resolvedNodeEnv = environmentSchema.parse(rawEnv.nodeEnv);

  const apiTimeout = rawEnv.apiTimeout
    ? parseInt(rawEnv.apiTimeout, 10)
    : 30000;

  const apiTimeoutLongRunning = rawEnv.apiTimeoutLongRunning
    ? parseInt(rawEnv.apiTimeoutLongRunning, 10)
    : 120000;

  const apiTimeoutConversation = rawEnv.apiTimeoutConversation
    ? parseInt(rawEnv.apiTimeoutConversation, 10)
    : 180000;

  return appConfigSchema.parse({
    appEnv: resolvedAppEnv,
    nodeEnv: resolvedNodeEnv,
    isDevelopment: resolvedAppEnv !== "production",
    isProduction: resolvedAppEnv === "production",
    apiTimeout,
    apiTimeoutLongRunning,
    apiTimeoutConversation,
  });
}

export const config = createConfig();

export default config;
