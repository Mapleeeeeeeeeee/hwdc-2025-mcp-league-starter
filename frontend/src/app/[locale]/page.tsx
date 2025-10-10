import { getTranslations } from "next-intl/server";

import { ChatShell } from "@/components/chat/ChatShell";
import { listServers } from "@/features/mcp";
import type { McpServersSnapshot } from "@/features/mcp";
import { config } from "@/lib/config";

type LocaleLandingPageProps = {
  params: Promise<{
    locale: string;
  }>;
};

export default async function LocaleLandingPage({
  params,
}: LocaleLandingPageProps) {
  const { locale } = await params;

  const tCommon = await getTranslations({
    locale,
    namespace: "common",
  });

  let initialSnapshot: McpServersSnapshot | undefined;

  try {
    initialSnapshot = await listServers();
  } catch (error) {
    if (config.isDevelopment) {
      console.error("Failed to prefetch MCP servers", error);
    }
  }

  return (
    <ChatShell
      title={tCommon("landing.title")}
      subtitle={tCommon("landing.subtitle")}
      initialMcpData={initialSnapshot}
    />
  );
}
