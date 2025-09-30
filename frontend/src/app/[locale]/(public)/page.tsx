import { getTranslations } from "next-intl/server";

import { LandingHero } from "@/components/chat/LandingHero";
import { ChatShell } from "@/components/chat/ChatShell";
import { ServerOverview } from "@/components/mcp/ServerOverview";
import { listServers } from "@/features/mcp";
import type { McpServersSnapshot } from "@/features/mcp";

export default async function LandingPage() {
  const tCommon = await getTranslations("common");

  let initialSnapshot: McpServersSnapshot | undefined;

  try {
    initialSnapshot = await listServers();
  } catch (error) {
    if (process.env.NODE_ENV !== "production") {
      console.error("Failed to prefetch MCP servers", error);
    }
  }

  return (
    <div className="flex flex-col gap-10">
      <LandingHero
        title={tCommon("landing.title")}
        subtitle={tCommon("landing.subtitle")}
        cta={tCommon("landing.cta")}
      />

      <ChatShell />

      <ServerOverview initialData={initialSnapshot} />
    </div>
  );
}
