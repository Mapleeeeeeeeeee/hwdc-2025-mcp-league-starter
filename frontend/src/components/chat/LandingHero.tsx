type LandingHeroProps = {
  title: string;
  subtitle: string;
  cta: string;
  badge: string;
  footerLabel: string;
};

export function LandingHero({
  title,
  subtitle,
  cta,
  badge,
  footerLabel,
}: LandingHeroProps) {
  return (
    <section className="relative overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-purple-600/30 via-blue-500/20 to-emerald-500/20 p-[1px]">
      <div className="relative rounded-[calc(1.5rem-1px)] bg-neutral-950/80 p-10 shadow-[0_20px_60px_-15px_rgba(0,0,0,0.6)]">
        <div className="flex flex-col gap-6 text-left lg:max-w-2xl">
          <span className="inline-flex w-fit items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs uppercase tracking-[0.4em] text-white/60">
            {badge}
          </span>
          <h1 className="text-4xl font-semibold leading-tight text-white md:text-5xl">
            {title}
          </h1>
          <p className="text-base text-white/70 md:text-lg">{subtitle}</p>
          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              className="inline-flex items-center gap-2 rounded-full bg-white px-6 py-2 text-sm font-semibold text-neutral-900 transition hover:bg-white/90"
            >
              {cta}
            </button>
            <span className="text-xs uppercase tracking-[0.4em] text-white/40">
              {footerLabel}
            </span>
          </div>
        </div>

        <div className="pointer-events-none absolute -right-16 -top-16 h-48 w-48 rounded-full bg-purple-500/40 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-20 right-14 h-40 w-40 rounded-full bg-emerald-400/40 blur-3xl" />
        <div className="pointer-events-none absolute -left-20 top-20 h-40 w-40 rounded-full bg-blue-400/40 blur-3xl" />
      </div>
    </section>
  );
}
