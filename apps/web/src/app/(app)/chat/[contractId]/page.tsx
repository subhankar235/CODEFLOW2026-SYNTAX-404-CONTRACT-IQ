"use client";

import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { ChatWindow } from "@/features/chat/ChatWindow";
import { useApiClient } from "@/lib/api";
import { SummaryResult } from "@/types/analysis";
import { Loader2, ArrowLeft, Shield, FileText } from "lucide-react";
import Link from "next/link";



export default function ChatPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const contractId = params?.contractId as string;
  const jobId = searchParams.get("job") || "";

  const { getContracts, getSummary } = useApiClient();
  const [contractName, setContractName] = useState("");
  const [summary, setSummary] = useState<SummaryResult | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!contractId) return;

    async function load() {
      try {
        // Fetch contract name
        const data = await getContracts();
        const contract = data.contracts.find((c) => c.id === contractId);
        if (contract) setContractName(contract.original_filename);

        // Fetch summary for compact risk context
        try {
          const s = await getSummary(contractId);
          if (s) setSummary(s);
        } catch {
          // Summary is optional context
        }
      } catch (err) {
        console.error("Failed to load contract info:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [contractId, getContracts, getSummary]);

  const riskScore = summary?.overall_risk_score ?? null;
  const contractType = summary?.contract_type ?? null;

  const getRiskColor = (score: number) => {
    if (score >= 70) return "text-red-400 bg-red-500/10 border-red-500/30";
    if (score >= 40) return "text-amber-400 bg-amber-500/10 border-amber-500/30";
    return "text-emerald-400 bg-emerald-500/10 border-emerald-500/30";
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] bg-[#030303]">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-zinc-800 bg-zinc-950/80 px-4 py-3 backdrop-blur-sm shrink-0">
        <div className="flex items-center gap-3">
          {/* Back button */}
          <Link
            href={jobId ? `/scan/${jobId}` : `/dashboard`}
            className="flex h-8 w-8 items-center justify-center rounded-full border border-zinc-800 text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>

          {/* Contract name + context */}
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-zinc-500 shrink-0" />
              <h1 className="text-sm font-semibold text-zinc-100 truncate max-w-[200px] sm:max-w-xs">
                {loading ? (
                  <span className="inline-block h-4 w-32 animate-pulse rounded bg-zinc-800" />
                ) : (
                  contractName || "Contract Q&A"
                )}
              </h1>
            </div>
            <p className="text-[10px] text-zinc-500 uppercase tracking-wider mt-0.5">
              AI Legal Assistant
            </p>
          </div>
        </div>

        {/* Risk score + contract type badges */}
        <div className="flex items-center gap-2">
          {contractType && (
            <span className="hidden sm:inline-flex items-center rounded-full border border-zinc-700 bg-zinc-900 px-2.5 py-1 text-xs font-medium text-zinc-400 capitalize">
              {contractType.replace(/_/g, " ")}
            </span>
          )}
          {riskScore !== null && (
            <span
              className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-semibold ${getRiskColor(riskScore)}`}
            >
              <Shield className="h-3 w-3" />
              {riskScore}% Risk
            </span>
          )}
        </div>
      </div>

      {/* Chat window */}
      <div className="flex-1 overflow-hidden">
        <ChatWindow contractId={contractId} jobId={jobId} />
      </div>
    </div>
  );
}