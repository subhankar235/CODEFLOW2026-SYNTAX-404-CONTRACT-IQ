"use client";

import Link from "next/link";
import { FileText, Clock, ChevronRight, MessageSquare } from "lucide-react";
import { DashboardContract } from "@/types/analysis";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface ContractCardProps {
  contract: DashboardContract;
  index: number;
}

export function ContractCard({ contract, index }: ContractCardProps) {
  const isComplete = contract.status === "complete";

  const getRiskStyles = (score: number) => {
    if (score <= 25) return "text-green-400 bg-green-500/10 border-green-500/20";
    if (score <= 60) return "text-yellow-400 bg-yellow-500/10 border-yellow-500/20";
    return "text-red-400 bg-red-500/10 border-red-500/20";
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
    >
      <Link
        href={isComplete ? `/scan/${contract.id}` : `/upload`}
        className="group block relative rounded-2xl border border-white/5 bg-white/[0.02] p-5 transition-all hover:bg-white/[0.05] hover:border-white/10"
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-500/10 group-hover:bg-blue-500/20 transition-colors">
              <FileText className="h-6 w-6 text-blue-400" />
            </div>
            <div>
              <h3 className="font-semibold text-zinc-100 group-hover:text-white transition-colors truncate max-w-[180px]">
                {contract.file_name}
              </h3>
              <div className="flex items-center gap-2 text-xs text-zinc-500 mt-1">
                <span className="uppercase tracking-wider">{contract.contract_type}</span>
                <span>•</span>
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {new Date(contract.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          </div>

          <div className="flex flex-col items-end gap-2">
            {!isComplete ? (
              <span className="inline-flex items-center rounded-full bg-blue-500/10 px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-widest text-blue-400 border border-blue-500/20 animate-pulse">
                Processing
              </span>
            ) : (
              <div className={cn(
                "inline-flex items-center rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-widest border",
                getRiskStyles(contract.overall_risk_score)
              )}>
                {contract.overall_risk_score} Score
              </div>
            )}
            <div className="flex items-center gap-2">
              <ChevronRight className="h-4 w-4 text-zinc-600 group-hover:text-zinc-400 transition-all group-hover:translate-x-0.5" />
            </div>
          </div>
        </div>

          {isComplete && (
            <div className="mt-4 flex items-center justify-between border-t border-white/5 pt-4">
              <span className="text-[11px] font-medium text-zinc-500">Verdict</span>
              <span className={cn(
                "text-[11px] font-bold uppercase tracking-wider",
                contract.should_sign === "yes_as-is" ? "text-green-400" :
                  contract.should_sign === "yes_with_changes" ? "text-yellow-400" : "text-red-400"
              )}>
                {contract.should_sign.replace(/_/g, ' ')}
              </span>
            </div>
          )}
      </Link>
    </motion.div>
  );
}
