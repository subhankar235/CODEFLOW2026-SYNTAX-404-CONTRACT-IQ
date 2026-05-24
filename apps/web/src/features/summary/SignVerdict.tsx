"use client";

import { motion } from "framer-motion";
import { ShouldSign } from "@/types/analysis";
import { cn } from "@/lib/utils";

interface SignVerdictProps {
  verdict: ShouldSign;
}

export function SignVerdict({ verdict }: SignVerdictProps) {
  const config: Record<ShouldSign, { label: string; color: string; bg: string }> = {
    "yes_as-is": {
      label: "YES AS-IS",
      color: "text-green-600 dark:text-green-400",
      bg: "bg-green-100 dark:bg-green-950/40",
    },
    "yes_with_changes": {
      label: "YES WITH CHANGES",
      color: "text-amber-600 dark:text-amber-400",
      bg: "bg-amber-100 dark:bg-amber-950/40",
    },
    "no": {
      label: "NO",
      color: "text-red-600 dark:text-red-400",
      bg: "bg-red-100 dark:bg-red-950/40",
    },
  };

  const { label, color, bg } = config[verdict] || config["no"];

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4, delay: 0.6 }}
      className={cn("rounded-2xl px-6 py-3 text-center", bg)}
    >
      <span className={cn("text-2xl font-extrabold tracking-tight", color)}>
        {label}
      </span>
    </motion.div>
  );
}
