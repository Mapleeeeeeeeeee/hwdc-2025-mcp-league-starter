import { ReactNode } from "react";
import { getMessages, setRequestLocale } from "next-intl/server";
import { notFound } from "next/navigation";

import { AppProviders } from "@/app/providers";
import type { AppLocale } from "@/lib/i18n/config";
import { LOCALES } from "@/lib/i18n/config";

type LocaleLayoutProps = {
  children: ReactNode;
  params: Promise<{
    locale: string;
  }>;
};

const SUPPORTED_LOCALES = new Set<AppLocale>(LOCALES);

export function generateStaticParams() {
  return LOCALES.map((locale) => ({ locale }));
}

export default async function LocaleLayout({
  children,
  params,
}: LocaleLayoutProps) {
  const { locale } = await params;

  if (!locale) {
    notFound();
  }

  const nextLocale = locale as AppLocale;

  if (!SUPPORTED_LOCALES.has(nextLocale)) {
    notFound();
  }

  setRequestLocale(nextLocale);

  const messages = await getMessages();

  return (
    <AppProviders locale={nextLocale} messages={messages}>
      {children}
    </AppProviders>
  );
}
