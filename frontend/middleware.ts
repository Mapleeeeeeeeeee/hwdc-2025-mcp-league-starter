import createMiddleware from "next-intl/middleware";

import { DEFAULT_LOCALE, LOCALE_PREFIX, LOCALES } from "./src/lib/i18n/config";

const intlMiddleware = createMiddleware({
  defaultLocale: DEFAULT_LOCALE,
  localePrefix: LOCALE_PREFIX,
  locales: LOCALES,
});

export default intlMiddleware;

export const config = {
  matcher: ["/", "/(zh-TW|en)/:path*"],
};
