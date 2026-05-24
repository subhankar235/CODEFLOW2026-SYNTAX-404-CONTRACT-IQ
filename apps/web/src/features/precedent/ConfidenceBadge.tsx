"use client";

import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

interface ConfidenceBadgeProps {
  score: number; // 0 to 100
}

export function ConfidenceBadge({ score }: ConfidenceBadgeProps) {
  const [displayScore, setDisplayScore] = useState(0);

  useEffect(() => {
    const duration = 800; // ms
    const startTime = performance.now();
    
    const update = (currentTime: number) => {
      const elapsed = currentTime - startTime;
      if (elapsed < duration) {
        setDisplayScore(Math.floor((elapsed / duration) * score));
        requestAnimationFrame(update);
      } else {
        setDisplayScore(score);
      }
    };
    requestAnimationFrame(update);
  }, [score]);

  const isHigh = score >= 75;
  const isMedium = score >= 50 && score < 75;
  const isLow = score < 50;

  return (
    <div className="flex flex-col items-center">
      <div
        className={cn(
          "flex h-16 w-16 items-center justify-center rounded-full border-4 font-bold tracking-tight shadow-sm transition-colors",
          isHigh ? "border-green-500 bg-green-50 text-green-700 dark:bg-green-950/20 dark:text-green-400" :
          isMedium ? "border-amber-500 bg-amber-50 text-amber-700 dark:bg-amber-950/20 dark:text-amber-400" :
          "border-red-500 bg-red-50 text-red-700 dark:bg-red-950/20 dark:text-red-400"
        )}
      >
        {displayScore}%
      </div>
      {isLow && (
        <span className="mt-2 text-xs font-medium text-red-600 dark:text-red-400">
          ⚠️ Verify with attorney
        </span>
      )}
    </div>
  );
}
