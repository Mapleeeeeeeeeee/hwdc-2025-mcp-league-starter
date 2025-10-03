import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";
import path from "path";
import { fileURLToPath } from "url";

const withNextIntl = createNextIntlPlugin("./src/i18n/request.ts");

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const nextConfig: NextConfig = {
  typedRoutes: true,
  // Fix workspace root detection warning for monorepo
  outputFileTracingRoot: path.join(__dirname, "../"),
  // Enable standalone output for Docker deployment
  output: "standalone",
};

export default withNextIntl(nextConfig);
