import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  experimental: {
    typedRoutes: true,
  },
  i18n: {
    locales: ["zh-TW", "en"],
    defaultLocale: "zh-TW",
  },
};

export default nextConfig;
