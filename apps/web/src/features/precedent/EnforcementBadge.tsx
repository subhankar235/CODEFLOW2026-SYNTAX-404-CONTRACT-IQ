import { cn } from "@/lib/utils";

interface EnforcementBadgeProps {
  likelihood: "Very Likely" | "Likely" | "Uncertain" | "Unlikely";
}

export function EnforcementBadge({ likelihood }: EnforcementBadgeProps) {
  const variants = {
    "Very Likely": "bg-red-100 text-red-800 border-red-200 dark:bg-red-900/30 dark:text-red-400 dark:border-red-800/50",
    "Likely": "bg-amber-100 text-amber-800 border-amber-200 dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-800/50",
    "Uncertain": "bg-yellow-100 text-yellow-800 border-yellow-200 dark:bg-yellow-900/30 dark:text-yellow-400 dark:border-yellow-800/50",
    "Unlikely": "bg-green-100 text-green-800 border-green-200 dark:bg-green-900/30 dark:text-green-400 dark:border-green-800/50",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-3 py-1 text-sm font-semibold uppercase tracking-wider",
        variants[likelihood] || variants["Uncertain"]
      )}
    >
      {likelihood}
    </span>
  );
}
