import { CheckCircle2 } from "lucide-react";
import { useScanStore } from "@/store/scanStore";

export function LeveragePoints() {
  const { powerResult } = useScanStore();

  const leveragePoints = powerResult?.leverage_points ?? [];
  if (!powerResult || leveragePoints.length === 0) {
    return null;
  }

  return (
    <div className="mt-8 space-y-4">
      <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
        Your Negotiating Leverage
      </h3>
      <ul className="space-y-3">
        {leveragePoints.map((point, index) => (
          <li key={index} className="flex items-start gap-3">
            <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-green-500" />
            <span className="text-sm leading-relaxed text-foreground/90">{point}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
