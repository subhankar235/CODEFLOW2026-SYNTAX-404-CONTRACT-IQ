"use client";

import { useScanStore } from "@/store/scanStore";
import { motion } from "framer-motion";

export function ScanProgress() {
  const { progressPct } = useScanStore();

  let phase = "Detecting risk patterns...";
  if (progressPct > 30) phase = "Running AI analysis...";
  if (progressPct > 70) phase = "Generating consequences...";
  if (progressPct >= 100) phase = "Finalizing report...";

  return (
    <div className="space-y-2 rounded-lg border bg-card/50 p-4">
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium text-foreground/80">{phase}</span>
        <span className="text-muted-foreground">{Math.round(progressPct)}%</span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
        <motion.div
          className="h-full bg-primary"
          initial={{ width: 0 }}
          animate={{ width: `${progressPct}%` }}
          transition={{ ease: "linear" }}
        />
      </div>
    </div>
  );
}
