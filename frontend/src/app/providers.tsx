"use client";

import { ReactNode, useMemo, useState } from "react";
import { NextIntlClientProvider } from "next-intl";
import {
  QueryClientProvider,
  HydrationBoundary,
  DehydratedState,
} from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";

import { createQueryClient } from "@/lib/query-client";
import type { AppLocale } from "@/lib/i18n/config";

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

  const memoizedMessages = useMemo(() => messages, [messages]);

  return (
    <NextIntlClientProvider locale={locale} messages={memoizedMessages}>
      <QueryClientProvider client={queryClient}>
        <HydrationBoundary state={dehydratedState}>
          {children}
        </HydrationBoundary>
        {process.env.NODE_ENV !== "production" ? (
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
