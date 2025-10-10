import { getTranslations } from "next-intl/server";

import { ChatShell } from "@/components/chat/ChatShell";

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

  return (
    <ChatShell
      title={tCommon("landing.title")}
      subtitle={tCommon("landing.subtitle")}
    />
  );
}
