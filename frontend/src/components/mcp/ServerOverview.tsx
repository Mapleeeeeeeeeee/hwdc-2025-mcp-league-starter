"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { motion, AnimatePresence } from "framer-motion";

import {
  useFetchMcpServers,
  useReloadAllMcpServers,
  useReloadMcpServer,
} from "@/features/mcp";
import type { McpServersSnapshot } from "@/features/mcp";
import { ApiError } from "@/lib/api/api-error";
import { cn } from "@/lib/utils";

type ServerOverviewProps = {
  initialData?: McpServersSnapshot;
};

export function ServerOverview({ initialData }: ServerOverviewProps) {
  const t = useTranslations("mcp.servers");
  const tErrors = useTranslations("errors");
  const [expandedServers, setExpandedServers] = useState<Set<string>>(
    new Set(),
  );

  const { data, isLoading, isFetching, isError, error, refresh } =
    useFetchMcpServers({ initialData });

  const {
    reload: reloadAll,
    isPending: isReloadingAll,
    isError: isReloadAllError,
    error: reloadAllError,
  } = useReloadAllMcpServers();

  const {
    reload: reloadServer,
    isPending: isReloadingServer,
    variables: reloadingServerName,
  } = useReloadMcpServer();

  const servers = data?.servers ?? [];
  const initialized = data?.initialized ?? false;

  const errorMessage = (() => {
    if (!(error instanceof ApiError)) {
      return tErrors("generic");
    }

    const scopedKey = error.i18nKey?.startsWith("errors.")
      ? error.i18nKey.slice("errors.".length)
      : error.i18nKey;

    if (scopedKey) {
      try {
        return tErrors(
          scopedKey as Parameters<typeof tErrors>[0],
          error.i18nParams as Parameters<typeof tErrors>[1],
        );
      } catch {
        // ignore and fallback
      }
    }

    return tErrors("generic");
  })();

  const toggleServerExpanded = (serverName: string) => {
    const newExpanded = new Set(expandedServers);
    if (newExpanded.has(serverName)) {
      newExpanded.delete(serverName);
    } else {
      newExpanded.add(serverName);
    }
    setExpandedServers(newExpanded);
  };

  return (
    <div className="flex flex-col space-y-4">
      {/* Header */}
      <header className="space-y-3">
        <div>
          <h3 className="text-base font-semibold tracking-tight text-white">
            {t("sectionTitle")}
          </h3>
          <p className="text-sm text-white/50">
            {initialized
              ? t("initialized", { count: servers.length })
              : t("initializing")}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => void refresh()}
            disabled={isFetching}
            className="flex-1 inline-flex items-center justify-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs font-medium text-white/80 transition hover:bg-white/10 disabled:pointer-events-none disabled:opacity-50"
          >
            <span
              className={`size-1.5 rounded-full ${isFetching ? "animate-pulse bg-emerald-300" : "bg-emerald-400/80"}`}
            />
            {isFetching ? t("refreshing") : t("refresh")}
          </button>
          <button
            type="button"
            onClick={() => void reloadAll()}
            disabled={isReloadingAll || isFetching}
            className="flex-1 inline-flex items-center justify-center gap-2 rounded-lg border border-orange-500/20 bg-orange-500/10 px-3 py-2 text-xs font-medium text-orange-300 transition hover:bg-orange-500/20 disabled:pointer-events-none disabled:opacity-50"
          >
            <svg
              className={`size-3.5 ${isReloadingAll ? "animate-spin" : ""}`}
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            {isReloadingAll ? t("reloading") : t("reloadAll")}
          </button>
        </div>
      </header>

      {/* Error Messages */}
      {isError && (
        <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-3 py-2 text-xs text-red-100">
          {errorMessage}
          {error instanceof ApiError && error.traceId && (
            <span className="ml-2 text-[10px] text-red-200/70">
              {t("traceLabel")}: {error.traceId}
            </span>
          )}
        </div>
      )}

      {isReloadAllError && reloadAllError && (
        <div className="rounded-lg border border-orange-500/40 bg-orange-500/10 px-3 py-2 text-xs text-orange-100">
          {t("reloadError")}
          {reloadAllError instanceof ApiError && reloadAllError.traceId && (
            <span className="ml-2 text-[10px] text-orange-200/70">
              {t("traceLabel")}: {reloadAllError.traceId}
            </span>
          )}
        </div>
      )}

      {/* Server List */}
      <div className="space-y-3">
        {isLoading && !initialData ? (
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, index) => (
              <div
                key={`skeleton-${index}`}
                className="h-20 animate-pulse rounded-lg border border-white/5 bg-white/5"
              />
            ))}
          </div>
        ) : (
          <div className="space-y-3">
            {servers.map((server) => {
              const isThisServerReloading =
                isReloadingServer && reloadingServerName === server.name;
              const isExpanded = expandedServers.has(server.name);

              return (
                <motion.div
                  key={server.name}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="rounded-lg border border-white/10 bg-white/5 backdrop-blur-sm transition-all hover:border-white/20 hover:bg-white/10"
                >
                  {/* Server Header */}
                  <div className="p-3">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-medium text-white/90 truncate">
                            {server.name}
                          </p>
                          <span
                            className={cn(
                              "inline-flex items-center gap-1 rounded-full px-1.5 py-0.5 text-[10px] font-medium",
                              server.connected
                                ? "bg-emerald-400/10 text-emerald-300"
                                : "bg-orange-400/10 text-orange-200",
                            )}
                          >
                            <span className="size-1 rounded-full bg-current" />
                            {server.connected
                              ? t("status.connected")
                              : t("status.disconnected")}
                          </span>
                        </div>
                        {server.description && (
                          <p className="mt-1 text-xs text-white/40 line-clamp-2">
                            {server.description}
                          </p>
                        )}
                      </div>

                      {server.enabled && (
                        <button
                          type="button"
                          onClick={() => void reloadServer(server.name)}
                          disabled={isReloadingServer || isFetching}
                          className="rounded-md border border-white/10 bg-white/5 p-1 text-white/70 transition hover:bg-white/10 disabled:pointer-events-none disabled:opacity-50"
                          title={t("reload")}
                        >
                          <svg
                            className={cn(
                              "size-3",
                              isThisServerReloading && "animate-spin",
                            )}
                            xmlns="http://www.w3.org/2000/svg"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                            />
                          </svg>
                        </button>
                      )}
                    </div>

                    {/* Server Stats */}
                    <div className="mt-2 flex items-center gap-3 text-xs">
                      <div className="flex items-center gap-1 text-white/60">
                        <span className="text-white/40">
                          {t("labels.functions")}:
                        </span>
                        <span className="font-semibold text-white">
                          {server.functionCount}
                        </span>
                      </div>
                      <div className="flex items-center gap-1 text-white/60">
                        <span className="text-white/40">
                          {t("labels.enabled")}:
                        </span>
                        <span
                          className={cn(
                            "font-semibold",
                            server.enabled
                              ? "text-emerald-300"
                              : "text-red-300",
                          )}
                        >
                          {server.enabled ? t("enabled.yes") : t("enabled.no")}
                        </span>
                      </div>
                    </div>

                    {/* Expand Functions Button */}
                    {server.functions.length > 0 && (
                      <button
                        type="button"
                        onClick={() => toggleServerExpanded(server.name)}
                        className="mt-2 flex w-full items-center justify-between rounded-md bg-white/5 px-2 py-1.5 text-xs text-white/60 transition hover:bg-white/10 hover:text-white/80"
                      >
                        <span>{t("labels.functionsList")}</span>
                        <motion.svg
                          animate={{ rotate: isExpanded ? 180 : 0 }}
                          transition={{ duration: 0.2 }}
                          className="h-3 w-3"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M19 9l-7 7-7-7"
                          />
                        </motion.svg>
                      </button>
                    )}
                  </div>

                  {/* Function List (Collapsible) */}
                  <AnimatePresence>
                    {isExpanded && server.functions.length > 0 && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="overflow-hidden border-t border-white/10"
                      >
                        <div className="p-3 pt-2">
                          <div className="flex flex-wrap gap-1">
                            {server.functions.map((fn) => (
                              <span
                                key={`${server.name}-${fn}`}
                                className="rounded-md border border-white/10 bg-white/5 px-1.5 py-0.5 text-[10px] text-white/60"
                              >
                                {fn}
                              </span>
                            ))}
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              );
            })}

            {servers.length === 0 && !isLoading && (
              <div className="rounded-lg border border-dashed border-white/20 bg-white/5 p-4 text-center text-sm text-white/60">
                {t("empty")}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
