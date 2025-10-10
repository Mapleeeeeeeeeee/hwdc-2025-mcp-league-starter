import { getTranslations } from "next-intl/server";

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
    <div className="flex gap-6 h-[calc(100vh-120px)]">
      {/* Main Content - ChatShell */}
      <div className="flex-1 min-w-0">
        <ChatShell
          title={tCommon("landing.title")}
          subtitle={tCommon("landing.subtitle")}
        />
      </div>

      {/* Right Sidebar - Server Overview */}
      <aside className="w-96 flex-shrink-0 overflow-hidden">
        <ServerOverview initialData={initialSnapshot} />
      </aside>
    </div>
  );
}
