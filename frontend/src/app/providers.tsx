"use client";

import { ReactNode, useState } from "react";
import { NextIntlClientProvider } from "next-intl";
import {
  QueryClientProvider,
  HydrationBoundary,
  DehydratedState,
} from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";

import { createQueryClient } from "@/lib/query-client";
import { config } from "@/lib/config";
import type { AppLocale } from "@/lib/i18n/config";
import { DEFAULT_TIME_ZONE } from "@/lib/i18n/config";

type AppProvidersProps = {
  children: ReactNode;
  locale: AppLocale;
  messages: Record<string, unknown>;
  dehydratedState?: DehydratedState;
};

export function AppProviders({
  children,
  locale,
  messages,
  dehydratedState,
}: AppProvidersProps) {
  const [queryClient] = useState(() => createQueryClient());

  return (
    <NextIntlClientProvider
      locale={locale}
      messages={messages}
      timeZone={DEFAULT_TIME_ZONE}
    >
      <QueryClientProvider client={queryClient}>
        <HydrationBoundary state={dehydratedState}>
          {children}
        </HydrationBoundary>
        {config.isDevelopment ? (
          <ReactQueryDevtools
            initialIsOpen={false}
            buttonPosition="bottom-right"
            position="bottom"
          />
        ) : null}
      </QueryClientProvider>
    </NextIntlClientProvider>
  );
}
