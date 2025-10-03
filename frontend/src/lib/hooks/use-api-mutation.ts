"use client";

import {
  useMutation,
  type UseMutationOptions,
  type UseMutationResult,
} from "@tanstack/react-query";

import { ApiError } from "@/lib/api/api-error";

export type UseApiMutationOptions<TData, TVariables> = Omit<
  UseMutationOptions<TData, ApiError, TVariables>,
  "mutationFn"
> & {
  mutationFn: (variables: TVariables) => Promise<TData>;
};

export function useApiMutation<TData, TVariables = void>(
  options: UseApiMutationOptions<TData, TVariables>,
): UseMutationResult<TData, ApiError, TVariables> {
  return useMutation(options);
}
