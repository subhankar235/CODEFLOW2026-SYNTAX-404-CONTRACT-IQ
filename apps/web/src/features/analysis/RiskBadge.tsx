import { RiskLevel } from "@/types/clause";
import { cn } from "@/lib/utils";

interface RiskBadgeProps {
  level: RiskLevel;
  className?: string;
}

export function RiskBadge({ level, className }: RiskBadgeProps) {
  const variants = {
    HIGH: "bg-red-500/15 text-red-700 border-red-500/30 dark:text-red-400",
    MEDIUM: "bg-amber-500/15 text-amber-700 border-amber-500/30 dark:text-amber-400",
    LOW: "bg-green-500/15 text-green-700 border-green-500/30 dark:text-green-400",
    SAFE: "bg-slate-500/15 text-slate-700 border-slate-500/30 dark:text-slate-400",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors",
        variants[level],
        className
      )}
    >
      {level}
    </span>
  );
}
