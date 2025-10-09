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

  // Development API proxy: route /api/* to backend server
  // In production, Nginx handles this routing
  async rewrites() {
    const isDevelopment = process.env.NODE_ENV !== "production";
    const backendUrl = process.env.DEV_BACKEND_URL || "http://localhost:8000";

    if (isDevelopment) {
      return [
        {
          source: "/api/:path*",
          destination: `${backendUrl}/api/:path*`,
        },
      ];
    }
    return [];
  },
};

export default withNextIntl(nextConfig);
