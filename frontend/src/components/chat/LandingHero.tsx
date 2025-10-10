"use client";

import { motion } from "framer-motion";
import { BackgroundBeams, AnimatedOrb } from "@/components/ui/BackgroundBeams";
import { AnimatedGradient } from "@/components/ui/AnimatedGradient";
import { fadeInUp, staggerContainer } from "@/lib/utils";

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
    <AnimatedGradient gradientClassName="from-purple-600 via-blue-500 to-emerald-500">
      <section className="relative overflow-hidden rounded-[calc(1.5rem-1px)] bg-neutral-950/80 shadow-[0_20px_60px_-15px_rgba(0,0,0,0.6)] backdrop-blur-xl">
        <div className="relative z-10 p-10">
          <motion.div
            variants={staggerContainer}
            initial="initial"
            animate="animate"
            className="flex flex-col gap-6 text-left lg:max-w-2xl"
          >
            {/* Badge with animation */}
            <motion.span
              variants={fadeInUp}
              className="inline-flex w-fit items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs uppercase tracking-[0.4em] text-white/60 backdrop-blur-sm transition-all hover:border-white/30 hover:bg-white/15"
            >
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
              </span>
              {badge}
            </motion.span>

            {/* Title with gradient animation */}
            <motion.h1
              variants={fadeInUp}
              className="bg-gradient-to-b from-white via-white to-white/60 bg-clip-text text-4xl font-bold leading-tight text-transparent md:text-6xl"
            >
              {title}
            </motion.h1>

            {/* Subtitle */}
            <motion.p
              variants={fadeInUp}
              className="text-base leading-relaxed text-white/70 md:text-lg"
            >
              {subtitle}
            </motion.p>

            {/* CTA section */}
            <motion.div
              variants={fadeInUp}
              className="flex flex-wrap items-center gap-3"
            >
              <motion.button
                type="button"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="group relative inline-flex items-center gap-2 overflow-hidden rounded-full bg-gradient-to-r from-emerald-400 to-blue-500 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-emerald-500/25 transition-all hover:shadow-xl hover:shadow-emerald-500/40"
              >
                <span className="relative z-10">{cta}</span>
                <motion.svg
                  className="relative z-10 h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  animate={{ x: [0, 3, 0] }}
                  transition={{
                    duration: 1.5,
                    repeat: Infinity,
                    ease: "easeInOut",
                  }}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 7l5 5m0 0l-5 5m5-5H6"
                  />
                </motion.svg>
                {/* Animated background overlay */}
                <motion.div
                  className="absolute inset-0 bg-gradient-to-r from-emerald-300 to-blue-400"
                  initial={{ x: "-100%" }}
                  whileHover={{ x: 0 }}
                  transition={{ duration: 0.3 }}
                />
              </motion.button>

              <motion.span
                variants={fadeInUp}
                className="text-xs uppercase tracking-[0.4em] text-white/40"
              >
                {footerLabel}
              </motion.span>
            </motion.div>
          </motion.div>
        </div>

        {/* Animated orbs */}
        <AnimatedOrb
          className="h-48 w-48 bg-purple-500/40 -right-16 -top-16"
          delay={0}
        />
        <AnimatedOrb
          className="h-40 w-40 bg-emerald-400/40 -bottom-20 right-14"
          delay={1}
        />
        <AnimatedOrb
          className="h-40 w-40 bg-blue-400/40 -left-20 top-20"
          delay={2}
        />

        {/* Background beams */}
        <BackgroundBeams className="opacity-60" />
      </section>
    </AnimatedGradient>
  );
}
