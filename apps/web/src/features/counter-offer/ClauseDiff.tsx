"use client";

import { useMemo } from "react";

interface ClauseDiffProps {
  originalText: string;
  rewrittenText: string;
  explanation: string;
}

export function ClauseDiff({ originalText, rewrittenText, explanation }: ClauseDiffProps) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {/* Original */}
        <div className="rounded-lg border bg-card p-4 shadow-sm">
          <div className="mb-2 flex items-center justify-between">
            <h4 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Original Clause</h4>
          </div>
          <div className="rounded bg-red-50 p-3 text-sm leading-relaxed text-red-900 dark:bg-red-950/20 dark:text-red-200">
            {originalText}
          </div>
        </div>

        {/* Rewrite */}
        <div className="rounded-lg border bg-card p-4 shadow-sm">
          <div className="mb-2 flex items-center justify-between">
            <h4 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Proposed Rewrite</h4>
          </div>
          <div className="rounded bg-green-50 p-3 text-sm leading-relaxed text-green-900 dark:bg-green-950/20 dark:text-green-200">
            {rewrittenText}
          </div>
        </div>
      </div>

      <div className="rounded-lg bg-blue-50/50 p-4 dark:bg-blue-950/20">
        <h4 className="mb-1 text-sm font-medium text-blue-900 dark:text-blue-300">Why this is better:</h4>
        <p className="text-sm leading-relaxed text-blue-800/80 dark:text-blue-200/80">{explanation}</p>
      </div>
    </div>
  );
}
