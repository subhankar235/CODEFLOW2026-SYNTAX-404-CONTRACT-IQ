import { BookOpen } from "lucide-react";
import NextLink from "next/link";

interface ClauseCitationProps {
  clauseId: string;
  jobId: string;
  label?: string;
}

export function ClauseCitation({
  clauseId,
  jobId,
  label = "View Referenced Clause",
}: ClauseCitationProps) {
  return (
    <NextLink
      href={`/scan/${jobId}?clause=${clauseId}`}
      className="inline-flex items-center gap-1.5 rounded-full border border-blue-500/30 bg-blue-500/10 px-3 py-1 text-xs font-medium text-blue-300 transition-all hover:border-blue-400/50 hover:bg-blue-500/20 hover:text-blue-200 active:scale-[0.97]"
    >
      <BookOpen className="h-3 w-3" />
      {label}
    </NextLink>
  );
}
