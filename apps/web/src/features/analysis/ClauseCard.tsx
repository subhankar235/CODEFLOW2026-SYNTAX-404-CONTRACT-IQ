import { Clause } from "@/types/clause";
import { RiskBadge } from "./RiskBadge";
import { cn } from "@/lib/utils";
import { useClauseStore } from "@/store/clauseStore";
import { motion } from "framer-motion";

interface ClauseCardProps {
  clause: Clause;
  onCardClick?: (clauseId: string) => void;
}

export function ClauseCard({ clause, onCardClick }: ClauseCardProps) {
  const { selectedClauseId, selectClause } = useClauseStore();
  const isSelected = selectedClauseId === clause.id;

  const formatCategory = (category: string) => {
    return category
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  const selectedRingClass = {
    HIGH: "ring-2 ring-red-500 bg-red-50/50 dark:bg-red-950/20",
    MEDIUM: "ring-2 ring-amber-500 bg-amber-50/50 dark:bg-amber-950/20",
    LOW: "ring-2 ring-green-500 bg-green-50/50 dark:bg-green-950/20",
    SAFE: "ring-2 ring-slate-500 bg-slate-50/50 dark:bg-slate-900/20",
  }[clause.risk_level];

  const handleClick = () => {
    selectClause(clause.id);
    if (onCardClick) {
      onCardClick(clause.id);
    }
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      whileHover={{ y: -2 }}
      onClick={handleClick}
      data-clause-id={clause.id}
      className={cn(
        "relative cursor-pointer rounded-xl border bg-card p-5 text-card-foreground shadow-sm transition-all hover:shadow-md",
        isSelected ? selectedRingClass : "hover:border-primary/50"
      )}
    >
      <div className="mb-3 flex items-start justify-between gap-4">
        <div className="flex flex-wrap items-center gap-2">
          <RiskBadge level={clause.risk_level} />
          <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
            {formatCategory(clause.risk_category)}
          </span>
        </div>
        {clause.confidence < 0.7 && (
          <span className="flex items-center gap-1 text-xs font-medium text-amber-600 dark:text-amber-500">
            ⚠️ Verify with attorney
          </span>
        )}
      </div>

      <div className="relative">
        <p className="text-sm leading-relaxed text-foreground/90">
          {clause.text.length > 120 ? clause.text.substring(0, 120) + "..." : clause.text}
        </p>
        {clause.text.length > 120 && (
          <div className="absolute bottom-0 left-0 h-8 w-full bg-gradient-to-t from-card to-transparent" />
        )}
      </div>
    </motion.div>
  );
}
