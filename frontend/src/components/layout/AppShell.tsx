import type { ReactNode } from "react";

import { LocaleSwitcher } from "@/components/i18n/LocaleSwitcher";

export function AppShell({ children }: { children: ReactNode }) {
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
            <LocaleSwitcher />
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
    </div>
  );
}
