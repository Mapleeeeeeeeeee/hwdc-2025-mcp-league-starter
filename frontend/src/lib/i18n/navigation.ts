import { createNavigation } from "next-intl/navigation";

import { DEFAULT_LOCALE, LOCALES } from "@/lib/i18n/config";

export const { Link, usePathname, useRouter, redirect } = createNavigation({
  locales: Array.from(LOCALES),
  defaultLocale: DEFAULT_LOCALE,
});
