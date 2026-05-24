"use client";

import { useScanStore } from "@/store/scanStore";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { LeveragePoints } from "./LeveragePoints";

export function PowerMeter() {
  const { powerResult } = useScanStore();

  if (!powerResult) {
    return (
      <div className="flex flex-col items-center justify-center space-y-6 rounded-xl border bg-card p-8 shadow-sm">
        <div className="h-40 w-full max-w-[300px] animate-pulse rounded-t-full bg-muted/50" />
        <div className="h-6 w-48 animate-pulse rounded bg-full bg-muted/50" />
        <div className="h-4 w-64 animate-pulse rounded bg-full bg-muted/50" />
      </div>
    );
  }

  const { power_score, power_label, key_imbalances } = powerResult;
  // Normalise to an array so downstream code never crashes on null/undefined
  const imbalances = key_imbalances ?? [];

  const rotation = (power_score / 100) * 90;

  const meterGradient = "conic-gradient(from 270deg at 50% 100%, #ef4444 0deg, #eab308 45deg, #22c55e 90deg, #eab308 135deg, #ef4444 180deg)";

  const isExtreme = Math.abs(power_score) > 60;
  const isModerate = Math.abs(power_score) > 20 && Math.abs(power_score) <= 60;

  return (
    <div className="rounded-xl border bg-card p-8 shadow-sm">
      <div className="flex flex-col items-center justify-center space-y-8">
        <div className="relative h-40 w-[300px] overflow-hidden">
          <div
            className="absolute top-0 left-0 h-[300px] w-[300px] rounded-full"
            style={{
              background: meterGradient,
              clipPath: "polygon(0 0, 100% 0, 100% 50%, 0 50%)"
            }}
          />
          <div className="absolute top-[30px] left-[30px] h-[240px] w-[240px] rounded-full bg-card" />
          
          <div className="absolute bottom-1 left-2 text-xs font-semibold text-red-600">-100</div>
          <div className="absolute bottom-1 right-2 text-xs font-semibold text-red-600">+100</div>
          <div className="absolute -top-1 left-1/2 -translate-x-1/2 text-xs font-semibold text-green-600">0</div>
          
          <motion.div
            initial={{ rotate: 0 }}
            animate={{ rotate: rotation }}
            transition={{
              type: "spring",
              stiffness: 60,
              damping: 15,
              mass: 1.5,
              restDelta: 0.001
            }}
            className="absolute bottom-0 left-1/2 h-[120px] w-2 -translate-x-1/2 origin-bottom"
          >
            <div className="absolute -top-2 left-1/2 -translate-x-1/2 h-0 w-0 border-b-[120px] border-l-[4px] border-r-[4px] border-b-slate-800 border-l-transparent border-r-transparent dark:border-b-slate-200" />
            <div className="absolute bottom-[-6px] left-1/2 h-3 w-3 -translate-x-1/2 rounded-full bg-slate-800 dark:bg-slate-200" />
          </motion.div>
        </div>

        <div className="text-center space-y-2">
          <h2 className={cn(
            "text-2xl font-bold tracking-tight",
            isExtreme ? "text-red-600 dark:text-red-500" :
            isModerate ? "text-amber-600 dark:text-amber-500" :
            "text-green-600 dark:text-green-500"
          )}>
            {power_label}
          </h2>
          
          {imbalances.length > 0 && (
            <p className="text-sm text-muted-foreground mx-auto max-w-[280px]">
              {imbalances[0].why}
            </p>
          )}
        </div>
      </div>

      <LeveragePoints />
    </div>
  );
}
