"use client";

import { useTranslations } from "next-intl";

import {
  useFetchMcpServers,
  useReloadAllMcpServers,
  useReloadMcpServer,
} from "@/features/mcp";
import type { McpServersSnapshot } from "@/features/mcp";
import { ApiError } from "@/lib/api/api-error";

type ServerOverviewProps = {
  initialData?: McpServersSnapshot;
};

export function ServerOverview({ initialData }: ServerOverviewProps) {
  const t = useTranslations("mcp.servers");
  const tErrors = useTranslations("errors");

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

  return (
    <section className="flex flex-col gap-4">
      <header className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">
            {t("sectionTitle")}
          </h2>
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
            className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-sm font-medium text-white/80 transition hover:bg-white/10 disabled:pointer-events-none disabled:opacity-50"
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
            className="inline-flex items-center gap-2 rounded-full border border-orange-500/20 bg-orange-500/10 px-3 py-1.5 text-sm font-medium text-orange-300 transition hover:bg-orange-500/20 disabled:pointer-events-none disabled:opacity-50"
          >
            <span
              className={`size-1.5 rounded-full ${isReloadingAll ? "animate-pulse bg-orange-300" : "bg-orange-400/80"}`}
            />
            {isReloadingAll ? t("reloading") : t("reloadAll")}
          </button>
        </div>
      </header>

      {isError ? (
        <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-100">
          {errorMessage}
          {error instanceof ApiError && error.traceId ? (
            <span className="ml-2 text-xs text-red-200/70">
              {t("traceLabel")}: {error.traceId}
            </span>
          ) : null}
        </div>
      ) : null}

      {isReloadAllError && reloadAllError ? (
        <div className="rounded-lg border border-orange-500/40 bg-orange-500/10 px-4 py-3 text-sm text-orange-100">
          {t("reloadError")}
          {reloadAllError instanceof ApiError && reloadAllError.traceId ? (
            <span className="ml-2 text-xs text-orange-200/70">
              {t("traceLabel")}: {reloadAllError.traceId}
            </span>
          ) : null}
        </div>
      ) : null}

      {isLoading && !initialData ? (
        <ul className="grid gap-3 md:grid-cols-2">
          {Array.from({ length: 4 }).map((_, index) => (
            <li
              key={`skeleton-${index}`}
              className="h-24 animate-pulse rounded-xl border border-white/5 bg-white/5"
            />
          ))}
        </ul>
      ) : (
        <ul className="grid gap-3 md:grid-cols-2">
          {servers.map((server) => {
            const isThisServerReloading =
              isReloadingServer && reloadingServerName === server.name;

            return (
              <li
                key={server.name}
                className="rounded-xl border border-white/10 bg-white/5 p-4"
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-white/90">
                      {server.name}
                    </p>
                    {server.description ? (
                      <p className="text-xs text-white/40">
                        {server.description}
                      </p>
                    ) : null}
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs font-medium ${server.connected ? "bg-emerald-400/10 text-emerald-300" : "bg-orange-400/10 text-orange-200"}`}
                    >
                      <span className="size-1.5 rounded-full bg-current" />
                      {server.connected
                        ? t("status.connected")
                        : t("status.disconnected")}
                    </span>
                    {server.enabled ? (
                      <button
                        type="button"
                        onClick={() => void reloadServer(server.name)}
                        disabled={isReloadingServer || isFetching}
                        className="rounded-md border border-white/10 bg-white/5 px-2 py-1 text-xs font-medium text-white/70 transition hover:bg-white/10 disabled:pointer-events-none disabled:opacity-50"
                        title={t("reload")}
                      >
                        {isThisServerReloading ? "⟳" : "↻"}
                      </button>
                    ) : null}
                  </div>
                </div>
                <dl className="mt-3 grid grid-cols-2 gap-2 text-xs text-white/50">
                  <div>
                    <dt className="uppercase tracking-[0.2em] text-white/40">
                      {t("labels.functions")}
                    </dt>
                    <dd className="text-base font-semibold text-white">
                      {server.functionCount}
                    </dd>
                  </div>
                  <div>
                    <dt className="uppercase tracking-[0.2em] text-white/40">
                      {t("labels.enabled")}
                    </dt>
                    <dd className="text-base font-semibold text-white">
                      {server.enabled ? t("enabled.yes") : t("enabled.no")}
                    </dd>
                  </div>
                </dl>

                {server.functions.length > 0 ? (
                  <div className="mt-3 border-t border-white/10 pt-3 text-xs text-white/60">
                    <p className="mb-1 font-semibold uppercase tracking-[0.2em] text-white/30">
                      {t("labels.functionsList")}
                    </p>
                    <ul className="flex flex-wrap gap-1">
                      {server.functions.map((fn) => (
                        <li
                          key={`${server.name}-${fn}`}
                          className="rounded-full border border-white/10 bg-white/10 px-2 py-0.5 text-[11px]"
                        >
                          {fn}
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </li>
            );
          })}

          {servers.length === 0 && !isLoading ? (
            <li className="rounded-xl border border-dashed border-white/20 bg-white/5 p-6 text-sm text-white/60">
              {t("empty")}
            </li>
          ) : null}
        </ul>
      )}
    </section>
  );
}
