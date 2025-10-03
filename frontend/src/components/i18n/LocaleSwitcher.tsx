"use client";

import { useTransition } from "react";
import { useLocale, useTranslations } from "next-intl";
import { useSearchParams } from "next/navigation";

import { usePathname, useRouter } from "@/lib/i18n/navigation";

import type { AppLocale } from "@/lib/i18n/config";
import { LOCALES } from "@/lib/i18n/config";

export function LocaleSwitcher() {
  const locale = useLocale() as AppLocale;
  const t = useTranslations("common.localeSwitcher");
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [isPending, startTransition] = useTransition();

  const handleChange = (nextLocale: AppLocale) => {
    if (nextLocale === locale) return;

    const queryEntries = searchParams
      ? Object.fromEntries(searchParams.entries())
      : undefined;

    startTransition(() => {
      router.replace({ pathname, query: queryEntries }, { locale: nextLocale });
    });
  };

  return (
    <label className="flex items-center gap-2 rounded-full border border-white/10 bg-white/10/30 px-3 py-1 text-xs text-white/70">
      <span className="font-semibold uppercase tracking-[0.3em] text-white/50">
        {t("label")}
      </span>
      <select
        className="bg-transparent text-white focus:outline-none"
        value={locale}
        onChange={(event) => handleChange(event.target.value as AppLocale)}
        disabled={isPending}
      >
        {LOCALES.map((code) => (
          <option key={code} value={code} className="text-black">
            {t(`options.${code}`)}
          </option>
        ))}
      </select>
    </label>
  );
}
