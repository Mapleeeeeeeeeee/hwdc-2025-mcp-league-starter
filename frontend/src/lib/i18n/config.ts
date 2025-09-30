export const LOCALES = ["zh-TW", "en"] as const;

export type AppLocale = (typeof LOCALES)[number];

export const DEFAULT_LOCALE: AppLocale = "zh-TW";

export const LOCALE_PREFIX = "always" as const;

export const DEFAULT_TIME_ZONE = "Asia/Taipei" as const;
