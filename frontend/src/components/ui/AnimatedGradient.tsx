"use client";

import React from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface AnimatedGradientProps {
  children: React.ReactNode;
  className?: string;
  /**
   * Gradient colors in Tailwind format (e.g., "from-purple-600 to-blue-500")
   */
  gradientClassName?: string;
}

/**
 * Animated gradient border wrapper component
 * Creates a smooth animated gradient border effect
 */
export function AnimatedGradient({
  children,
  className,
  gradientClassName = "from-purple-600 via-blue-500 to-emerald-500",
}: AnimatedGradientProps) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className={cn("relative overflow-hidden rounded-3xl p-[1px]", className)}
    >
      {/* Animated gradient background */}
      <motion.div
        animate={{
          backgroundPosition: ["0% 50%", "100% 50%", "0% 50%"],
        }}
        transition={{
          duration: 5,
          repeat: Infinity,
          ease: "linear",
        }}
        className={cn("absolute inset-0 bg-gradient-to-r", gradientClassName)}
        style={{
          backgroundSize: "200% 200%",
        }}
      />

      {/* Content wrapper */}
      <div className="relative">{children}</div>
    </motion.div>
  );
}
