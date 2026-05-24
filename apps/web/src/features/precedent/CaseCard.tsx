import { cn } from "@/lib/utils";
import { Gavel } from "lucide-react";

interface CaseCardProps {
  caseName: string;
  year: number;
  jurisdiction: string;
  outcome: string;
}

export function CaseCard({ caseName, year, jurisdiction, outcome }: CaseCardProps) {
  // Simple heuristic for favorable if backend doesn't provide
  const isFavorable = outcome.toLowerCase().includes("unenforceable") || outcome.toLowerCase().includes("struck down") || outcome.toLowerCase().includes("favor");

  return (
    <div className="flex flex-col space-y-2 rounded-lg border bg-card p-4 shadow-sm transition-shadow hover:shadow-md">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h4 className="flex items-center gap-2 font-bold text-foreground">
            <Gavel className="h-4 w-4 text-muted-foreground" />
            {caseName}
          </h4>
          <p className="mt-1 text-xs font-medium text-muted-foreground">
            {jurisdiction} • {year}
          </p>
        </div>
      </div>
      <div
        className={cn(
          "rounded-md p-2.5 text-sm font-medium leading-relaxed",
          isFavorable
            ? "bg-green-50 text-green-800 dark:bg-green-950/20 dark:text-green-300"
            : "bg-red-50 text-red-800 dark:bg-red-950/20 dark:text-red-300"
        )}
      >
        {outcome}
      </div>
    </div>
  );
}
