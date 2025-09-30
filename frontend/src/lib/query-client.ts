import { QueryClient } from "@tanstack/react-query";

import { ApiError } from "@/lib/api/api-error";

export function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        gcTime: 5 * 60_000,
        refetchOnWindowFocus: false,
        retry: (failureCount, error) => {
          if (error instanceof ApiError && error.tooManyRequests()) {
            return false;
          }

          return failureCount < 2;
        },
      },
      mutations: {
        retry: 1,
      },
    },
  });
}
