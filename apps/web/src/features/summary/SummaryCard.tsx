"use client";

import { motion } from "framer-motion";
import { RiskScoreMeter } from "./RiskScoreMeter";
import { SignVerdict } from "./SignVerdict";
import { useScanStore } from "@/store/scanStore";
import { CheckCircle2, XCircle } from "lucide-react";
import { SummaryResult } from "@/types/analysis";

interface SummaryCardProps {
  data: SummaryResult;
}

export function SummaryCard({ data }: SummaryCardProps) {
  const { negotiating_power } = data;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="w-full rounded-2xl border bg-card p-6 shadow-sm"
    >
      <div className="flex flex-col lg:flex-row items-center gap-6">
        <div className="flex flex-col items-center gap-4">
          <RiskScoreMeter score={data.overall_risk_score} />
          <div className="text-center space-y-1">
            <SignVerdict verdict={data.should_you_sign} />
            <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
              {negotiating_power} Negotiating Power
            </p>
          </div>
        </div>

        <div className="flex-1 w-full space-y-6">
          <div>
            <p className="italic text-sm text-muted-foreground leading-relaxed">
              &ldquo;{data.one_liner}&rdquo;
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-3">
              <h3 className="text-sm font-semibold uppercase tracking-widest text-red-600 dark:text-red-500">
                Key Concerns
              </h3>
              <ul className="space-y-2">
                {data.top_3_concerns.map((concern, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <XCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-500" />
                    <span>{concern}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="space-y-3">
              <h3 className="text-sm font-semibold uppercase tracking-widest text-green-600 dark:text-green-500">
                Positives
              </h3>
              <ul className="space-y-2">
                {data.top_2_positives.map((positive, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-green-500" />
                    <span>{positive}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

export function SummaryCardSkeleton() {
  return (
    <div className="w-full rounded-2xl border bg-card p-6 shadow-sm animate-pulse">
      <div className="flex flex-col lg:flex-row items-center gap-6">
        <div className="flex flex-col items-center gap-4">
          <div className="h-[140px] w-[140px] rounded-full bg-muted/50" />
          <div className="h-12 w-36 rounded-xl bg-muted/50" />
        </div>
        <div className="flex-1 w-full space-y-6">
          <div className="h-6 w-3/4 rounded bg-muted/50" />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-3">
              <div className="h-4 w-24 rounded bg-muted/50" />
              <div className="space-y-2">
                <div className="h-4 w-full rounded bg-muted/50" />
                <div className="h-4 w-5/6 rounded bg-muted/50" />
                <div className="h-4 w-4/6 rounded bg-muted/50" />
              </div>
            </div>
            <div className="space-y-3">
              <div className="h-4 w-24 rounded bg-muted/50" />
              <div className="space-y-2">
                <div className="h-4 w-full rounded bg-muted/50" />
                <div className="h-4 w-5/6 rounded bg-muted/50" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
