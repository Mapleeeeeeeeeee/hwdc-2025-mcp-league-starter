import { getRequestConfig } from "next-intl/server";

import type { AppLocale } from "@/lib/i18n/config";
import { LOCALES, DEFAULT_LOCALE } from "@/lib/i18n/config";
import { config } from "@/lib/config";

type Messages = Record<string, unknown>;

function isSupportedLocale(locale: string): locale is AppLocale {
  return (LOCALES as readonly string[]).includes(locale);
}

export default getRequestConfig(async ({ requestLocale }) => {
  // Await the requestLocale promise
  const locale = await requestLocale;

  if (config.isDevelopment) {
    console.log("[i18n/request] requested locale", locale);
  }

  const resolvedLocale =
    locale && isSupportedLocale(locale) ? locale : DEFAULT_LOCALE;

  const messagesModule: { default: Messages } = await import(
    `@/messages/${resolvedLocale}/index`
  );

  return {
    locale: resolvedLocale,
    messages: messagesModule.default,
  };
});
