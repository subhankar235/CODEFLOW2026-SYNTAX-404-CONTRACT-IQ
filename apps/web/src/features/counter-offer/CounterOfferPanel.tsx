"use client";

import { useState, useCallback } from "react";
import { Clause } from "@/types/clause";
import { useApiClient } from "@/lib/api";
import { Loader2, RefreshCw } from "lucide-react";
import { VersionTabs } from "./VersionTabs";
import { ClauseDiff } from "./ClauseDiff";
import { NegotiationEmail } from "./NegotiationEmail";
import { CounterOffer } from "@/types/api";

interface CounterOfferPanelProps {
  clause: Clause;
}

export function CounterOfferPanel({ clause }: CounterOfferPanelProps) {
  const [status, setStatus] = useState<"idle" | "generating" | "ready" | "error">("idle");
  const [counterOffer, setCounterOffer] = useState<CounterOffer | null>(null);
  const [activeVersionIndex, setActiveVersionIndex] = useState(1);
  const { generateCounterOffer, getCounterOffer } = useApiClient();

  const handleGenerate = useCallback(async () => {
    setStatus("generating");

    try {
      await generateCounterOffer(clause.id);

      const interval = setInterval(async () => {
        try {
          const result = await getCounterOffer(clause.id);
          // Check if result has the expected data (not just a status="processing" placeholder)
          if (result && "aggressive_clause" in result && result.aggressive_clause) {
            setCounterOffer(result);
            setStatus("ready");
            clearInterval(interval);
          }
        } catch {
        }
      }, 3000);

      setTimeout(() => {
        clearInterval(interval);
        if (status === "generating") setStatus("error");
      }, 60000);
    } catch {
      setStatus("error");
    }
  }, [clause.id, generateCounterOffer, getCounterOffer]);

  if (status === "idle") {
    return (
      <div className="flex h-full flex-col items-center justify-center space-y-4 p-8 text-center">
        <p className="text-muted-foreground">
          This clause exposes you to significant risk. Generate a professionally worded counter-offer to push back.
        </p>
        <button
          onClick={handleGenerate}
          className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow transition-colors hover:bg-primary/90"
        >
          Generate Counter-Offer
        </button>
      </div>
    );
  }

  if (status === "generating") {
    return (
      <div className="flex h-full flex-col items-center justify-center space-y-4 p-8 text-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <p className="animate-pulse text-sm font-medium text-muted-foreground">
          Generating counter-offer strategies using AI...
        </p>
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className="flex h-full flex-col items-center justify-center space-y-4 p-8 text-center">
        <p className="text-sm text-red-500">Failed to generate counter-offer.</p>
        <button
          onClick={handleGenerate}
          className="flex items-center gap-2 rounded-md border bg-background px-4 py-2 text-sm font-medium shadow-sm hover:bg-muted"
        >
          <RefreshCw className="h-4 w-4" /> Try Again
        </button>
      </div>
    );
  }

  if (!counterOffer) return null;

  const versionsData = [
    { strategy: "Conservative", text: counterOffer.conservative_clause, explanation: counterOffer.explanation_conservative },
    { strategy: "Balanced", text: counterOffer.balanced_clause, explanation: counterOffer.explanation_balanced },
    { strategy: "Aggressive", text: counterOffer.aggressive_clause, explanation: counterOffer.explanation_aggressive },
  ];

  const versions = versionsData.map((v) => v.strategy);
  const activeVersion = versionsData[activeVersionIndex] || versionsData[1];

  return (
    <div className="space-y-6 p-4">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h3 className="text-lg font-semibold text-foreground">Drafted Counter-Offer</h3>
          <p className="text-sm text-muted-foreground">Select a negotiation strategy</p>
        </div>
        <VersionTabs
          versions={versions}
          activeVersion={activeVersion.strategy}
          onSelect={(v) => setActiveVersionIndex(versions.findIndex((x) => x === v))}
        />
      </div>

      <ClauseDiff
        originalText={clause.text}
        rewrittenText={activeVersion.text}
        explanation={activeVersion.explanation}
      />

      <div className="border-t pt-4">
        <NegotiationEmail emailBody={counterOffer.negotiation_email} />
      </div>
    </div>
  );
}