import { getTranslations } from "next-intl/server";

import { LandingHero } from "@/components/chat/LandingHero";
import { ChatShell } from "@/components/chat/ChatShell";
import { ServerOverview } from "@/components/mcp/ServerOverview";
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
    <div className="flex flex-col gap-10">
      <LandingHero
        title={tCommon("landing.title")}
        subtitle={tCommon("landing.subtitle")}
        cta={tCommon("landing.cta")}
        badge={tCommon("landing.badge")}
        footerLabel={tCommon("landing.protocol")}
      />

      <ChatShell />

      <ServerOverview initialData={initialSnapshot} />
    </div>
  );
}
