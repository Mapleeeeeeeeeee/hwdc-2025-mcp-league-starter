import { ReactNode } from "react";
import { getMessages, setRequestLocale } from "next-intl/server";
import { notFound } from "next/navigation";
import { Geist, Geist_Mono } from "next/font/google";

import { AppProviders } from "@/app/providers";
import { AppShell } from "@/components/layout/AppShell";
import type { AppLocale } from "@/lib/i18n/config";
import { LOCALES } from "@/lib/i18n/config";
import { config } from "@/lib/config";

import "../globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
  display: "swap",
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
  display: "swap",
});

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

  if (config.isDevelopment) {
    console.log("[LocaleLayout] locale resolved", nextLocale);
  }

  setRequestLocale(nextLocale);

  const messages = await getMessages();

  return (
    <html lang={nextLocale} suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} bg-neutral-950 text-neutral-50 antialiased`}
      >
        <AppProviders locale={nextLocale} messages={messages}>
          <AppShell>{children}</AppShell>
        </AppProviders>
      </body>
    </html>
  );
}
