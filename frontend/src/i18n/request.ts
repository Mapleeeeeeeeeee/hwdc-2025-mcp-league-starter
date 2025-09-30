import { getRequestConfig } from "next-intl/server";
import { notFound } from "next/navigation";

import type { AppLocale } from "@/lib/i18n/config";
import { LOCALES } from "@/lib/i18n/config";

type Messages = Record<string, unknown>;

function isSupportedLocale(locale: string): locale is AppLocale {
  return (LOCALES as readonly string[]).includes(locale);
}

export default getRequestConfig(async ({ locale }) => {
  if (!locale || !isSupportedLocale(locale)) {
    notFound();
  }

  const messagesModule: { default: Messages } = await import(
    `@/messages/${locale}/index`
  );

  return {
    locale,
    messages: messagesModule.default,
  };
});
