"use client";

import { useClauseStore } from "@/store/clauseStore";
import { ClauseCard } from "./ClauseCard";
import { RiskCounter } from "./RiskCounter";
import { ScanProgress } from "./ScanProgress";
import { useScanStore } from "@/store/scanStore";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { RiskLevel } from "@/types/clause";

interface ClauseListProps {
  onCardClick?: (clauseId: string) => void;
}

export function ClauseList({ onCardClick }: ClauseListProps) {
  const { clauses, filter, setFilter } = useClauseStore();
  const { status } = useScanStore();
  
  const filteredClauses = clauses
    .filter((c) => filter === "ALL" || c.risk_level === filter)
    .sort((a, b) => a.position_index - b.position_index);

  const filterOptions: Array<RiskLevel | "ALL"> = ["ALL", "HIGH", "MEDIUM", "LOW", "SAFE"];

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className="mb-4 shrink-0 space-y-4">
        {status === "processing" && <ScanProgress />}
        
        <RiskCounter />
        
        <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-hide">
          {filterOptions.map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={cn(
                "rounded-full px-4 py-1.5 text-sm font-medium transition-colors",
                filter === f
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "bg-muted text-muted-foreground hover:bg-muted/80"
              )}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto pr-2 pb-24 scrollbar-thin">
        <div className="flex flex-col gap-4">
          <AnimatePresence mode="popLayout">
            {filteredClauses.map((clause, index) => {
              const isNew = !clause.id.includes("-");
              return (
                <motion.div
                  key={clause.id}
                  initial={{ opacity: 0, y: 30 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  transition={{
                    duration: 0.3,
                    delay: isNew ? index * 0.05 : 0,
                    ease: "easeOut",
                  }}
                  layout
                >
                  <ClauseCard
                    clause={clause}
                    onCardClick={onCardClick}
                  />
                </motion.div>
              );
            })}
          </AnimatePresence>
          {filteredClauses.length === 0 && (
            <div className="mt-8 text-center text-sm text-muted-foreground">
              No clauses found for this filter.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
