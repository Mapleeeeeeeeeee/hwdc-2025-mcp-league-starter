"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface LanguageToggleProps {
  value: string;
  onChange: (value: string) => void;
  options: Array<{ value: string; label: string }>;
  disabled?: boolean;
}

/**
 * Modern toggle switch for language selection
 * Clean, minimal design for better UX
 */
export function LanguageToggle({
  value,
  onChange,
  options,
  disabled = false,
}: LanguageToggleProps) {
  return (
    <div className="flex items-center gap-1 rounded-full border border-white/10 bg-white/5 p-1 backdrop-blur-sm">
      {options.map((option) => {
        const isSelected = value === option.value;

        return (
          <button
            key={option.value}
            type="button"
            onClick={() => onChange(option.value)}
            disabled={disabled}
            className={cn(
              "relative px-3 py-1.5 text-xs font-semibold transition-colors",
              "rounded-full outline-none focus:outline-none",
              disabled && "cursor-not-allowed opacity-50",
              isSelected ? "text-white" : "text-white/50 hover:text-white/70",
            )}
          >
            {isSelected && (
              <motion.div
                layoutId="language-toggle-bg"
                className="absolute inset-0 rounded-full bg-gradient-to-r from-emerald-500 to-blue-500"
                transition={{
                  type: "spring",
                  stiffness: 380,
                  damping: 30,
                }}
              />
            )}
            <span className="relative z-10">{option.label}</span>
          </button>
        );
      })}
    </div>
  );
}
