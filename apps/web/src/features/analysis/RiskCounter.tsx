"use client";

import { useClauseStore } from "@/store/clauseStore";
import { motion } from "framer-motion";

export function RiskCounter() {
  const { clauses } = useClauseStore();

  const highCount = clauses.filter((c) => c.risk_level === "HIGH").length;
  const mediumCount = clauses.filter((c) => c.risk_level === "MEDIUM").length;
  const safeCount = clauses.filter((c) => c.risk_level === "SAFE" || c.risk_level === "LOW").length;

  return (
    <div className="flex items-center gap-4 text-sm font-semibold tracking-tight">
      <div className="flex items-center gap-1.5 text-red-600 dark:text-red-400">
        <motion.span key={highCount} initial={{ y: -10, opacity: 0 }} animate={{ y: 0, opacity: 1 }}>
          {highCount}
        </motion.span>
        <span>HIGH</span>
      </div>
      <span className="text-muted-foreground/30">•</span>
      <div className="flex items-center gap-1.5 text-amber-600 dark:text-amber-500">
        <motion.span key={mediumCount} initial={{ y: -10, opacity: 0 }} animate={{ y: 0, opacity: 1 }}>
          {mediumCount}
        </motion.span>
        <span>MEDIUM</span>
      </div>
      <span className="text-muted-foreground/30">•</span>
      <div className="flex items-center gap-1.5 text-green-600 dark:text-green-500">
        <motion.span key={safeCount} initial={{ y: -10, opacity: 0 }} animate={{ y: 0, opacity: 1 }}>
          {safeCount}
        </motion.span>
        <span>SAFE</span>
      </div>
    </div>
  );
}
