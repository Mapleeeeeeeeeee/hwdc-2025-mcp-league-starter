"use client";

import { useTransition } from "react";
import { useLocale, useTranslations } from "next-intl";
import { useSearchParams } from "next/navigation";

import { usePathname, useRouter } from "@/lib/i18n/navigation";
import { LanguageToggle } from "@/components/ui/LanguageToggle";

import type { AppLocale } from "@/lib/i18n/config";
import { LOCALES } from "@/lib/i18n/config";

export function LocaleSwitcher() {
  const locale = useLocale() as AppLocale;
  const t = useTranslations("common.localeSwitcher");
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [isPending, startTransition] = useTransition();

  const handleChange = (nextLocale: string) => {
    if (nextLocale === locale) return;

    const queryEntries = searchParams
      ? Object.fromEntries(searchParams.entries())
      : undefined;

    startTransition(() => {
      router.replace(
        { pathname, query: queryEntries },
        { locale: nextLocale as AppLocale },
      );
    });
  };

  const options = LOCALES.map((code) => ({
    value: code,
    label: t(`options.${code}`),
  }));

  return (
    <LanguageToggle
      value={locale}
      onChange={handleChange}
      options={options}
      disabled={isPending}
    />
  );
}
