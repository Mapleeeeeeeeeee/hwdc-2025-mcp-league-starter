"use client";

import {
  QueryKey,
  useQuery,
  type UseQueryOptions,
  type UseQueryResult,
} from "@tanstack/react-query";

import { ApiError } from "@/lib/api/api-error";

export type UseApiOptions<TQueryFnData, TData = TQueryFnData> = (
  & Omit<
    UseQueryOptions<TQueryFnData, ApiError, TData, QueryKey>,
    "queryFn" | "queryKey"
  >
  & {
    queryKey: QueryKey;
    queryFn: () => Promise<TQueryFnData>;
  }
);

export function useApi<TQueryFnData, TData = TQueryFnData>(
  options: UseApiOptions<TQueryFnData, TData>,
): UseQueryResult<TData, ApiError> {
  return useQuery({
    refetchOnWindowFocus: false,
    ...options,
  });
}
