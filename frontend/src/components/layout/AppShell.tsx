"use client";

import type { ReactNode } from "react";
import { Suspense, useState } from "react";

import { LocaleSwitcher } from "@/components/i18n/LocaleSwitcher";
import { MCPSettingsDrawer } from "@/components/mcp/MCPSettingsDrawer";

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const [isMCPDrawerOpen, setIsMCPDrawerOpen] = useState(false);

  return (
    <div className="flex min-h-screen flex-col bg-gradient-to-b from-neutral-950 via-neutral-930 to-neutral-960 text-neutral-50">
      <header className="border-b border-white/10 bg-neutral-950/30 backdrop-blur-sm">
        <div className="mx-auto flex w-full max-w-5xl items-center justify-between px-6 py-4">
          <span className="text-sm font-semibold uppercase tracking-[0.4em] text-white/70">
            HWDC 2025
          </span>
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-white/60">
              MCP League Starter
            </span>

            {/* MCP Settings Button */}
            <button
              type="button"
              onClick={() => setIsMCPDrawerOpen(true)}
              className="group relative flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs font-medium text-white/80 transition hover:border-emerald-500/50 hover:bg-white/10"
              title="MCP 設定"
            >
              <svg
                className="h-4 w-4 transition group-hover:text-emerald-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                />
              </svg>
              <span className="hidden sm:inline">MCP</span>
            </button>

            <Suspense
              fallback={
                <div className="h-6 w-20 animate-pulse rounded bg-white/10" />
              }
            >
              <LocaleSwitcher />
            </Suspense>
          </div>
        </div>
      </header>
      <main className="flex-1">
        <div className="mx-auto w-full max-w-5xl px-6 py-10 lg:py-16">
          {children}
        </div>
      </main>
      <footer className="border-t border-white/10 bg-neutral-950/40">
        <div className="mx-auto flex w-full max-w-5xl items-center justify-between px-6 py-4 text-xs text-white/40">
          <span>© {new Date().getFullYear()} HWDC</span>
          <span>Frontend MVP</span>
        </div>
      </footer>

      {/* MCP Settings Drawer */}
      <MCPSettingsDrawer
        isOpen={isMCPDrawerOpen}
        onClose={() => setIsMCPDrawerOpen(false)}
      />
    </div>
  );
}
