"use client";

import { useEffect, useRef } from "react";
import { motion, useInView, AnimatePresence } from "framer-motion";
import { CheckCircle2, XCircle } from "lucide-react";
import { useScanStore } from "@/store/scanStore";

const DIMENSION_COLORS: Record<string, string> = {
  Financial: "bg-red-100 text-red-700 dark:bg-red-950/40 dark:text-red-400",
  Liability: "bg-orange-100 text-orange-700 dark:bg-orange-950/40 dark:text-orange-400",
  IP: "bg-purple-100 text-purple-700 dark:bg-purple-950/40 dark:text-purple-400",
  "Exit Rights": "bg-blue-100 text-blue-700 dark:bg-blue-950/40 dark:text-blue-400",
  Obligations: "bg-amber-100 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400",
};

function getDimension(text: string): string {
  const lower = text.toLowerCase();
  if (lower.includes("financial") || lower.includes("$") || lower.includes("payment")) return "Financial";
  if (lower.includes("liability") || lower.includes("indemnify") || lower.includes("damages")) return "Liability";
  if (lower.includes("intellectual") || lower.includes("ip ") || lower.includes("patent") || lower.includes("copyright")) return "IP";
  if (lower.includes("exit") || lower.includes("termination") || lower.includes("renewal")) return "Exit Rights";
  return "Obligations";
}

interface ProsConsSnapshotProps {
  topConcerns: string[];
  topPositives: string[];
  verdict: string;
}

export function ProsConsSnapshot({ topConcerns, topPositives, verdict }: ProsConsSnapshotProps) {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });

  const concerns = topConcerns.slice(0, 3);
  const positives = topPositives.slice(0, 3);
  const total = Math.max(concerns.length, positives.length);

  return (
    <div ref={ref} className="w-full rounded-2xl border bg-card p-6 shadow-sm">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div>
          <h3 className="mb-4 flex items-center gap-2 text-lg font-bold text-green-600 dark:text-green-400">
            <CheckCircle2 className="h-5 w-5" />
            Pros
          </h3>
          <ul className="space-y-4">
            {positives.map((item, i) => {
              const dim = getDimension(item);
              return (
                <AnimatePresence key={i}>
                  {isInView && (
                    <motion.li
                      initial={{ opacity: 0, x: -30 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.4, delay: i * 0.08 }}
                      className="flex items-start gap-3"
                    >
                      <span className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-semibold ${DIMENSION_COLORS[dim]}`}>
                        {dim}
                      </span>
                      <span className="text-sm leading-relaxed">{item}</span>
                    </motion.li>
                  )}
                </AnimatePresence>
              );
            })}
          </ul>
        </div>

        <div>
          <h3 className="mb-4 flex items-center gap-2 text-lg font-bold text-red-600 dark:text-red-400">
            <XCircle className="h-5 w-5" />
            Cons
          </h3>
          <ul className="space-y-4">
            {concerns.map((item, i) => {
              const dim = getDimension(item);
              return (
                <AnimatePresence key={i}>
                  {isInView && (
                    <motion.li
                      initial={{ opacity: 0, x: 30 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.4, delay: i * 0.08 }}
                      className="flex items-start gap-3"
                    >
                      <span className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-semibold ${DIMENSION_COLORS[dim]}`}>
                        {dim}
                      </span>
                      <span className="text-sm leading-relaxed">{item}</span>
                    </motion.li>
                  )}
                </AnimatePresence>
              );
            })}
          </ul>
        </div>
      </div>

      {verdict && (
        <div className="mt-6 border-t pt-4">
          <p className="italic text-sm text-muted-foreground">&ldquo;{verdict}&rdquo;</p>
        </div>
      )}
    </div>
  );
}
