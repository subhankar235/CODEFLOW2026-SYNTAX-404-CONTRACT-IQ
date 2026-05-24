"use client";

import { useEffect, useCallback } from "react";
import { useAuth } from "@clerk/nextjs";
import { useSSE, ClauseResult } from "@/hooks/useSSE";
import { useClauseStore } from "@/store/clauseStore";
import { useScanStore } from "@/store/scanStore";
import { Clause, RiskLevel, RiskCategory } from "@/types/clause";
import { useApiClient } from "@/lib/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function mapRiskLevel(s: string): RiskLevel {
  const upper = s.toUpperCase();
  if (upper === "HIGH") return "HIGH";
  if (upper === "MEDIUM") return "MEDIUM";
  if (upper === "LOW") return "LOW";
  return "SAFE";
}

function mapRiskCategory(cats: string[]): RiskCategory {
  if (!cats || cats.length === 0) return "other";
  const cat = cats[0].toLowerCase();
  if (cat.includes("indemnity")) return "indemnity";
  if (cat.includes("ip") || cat.includes("intellectual")) return "ip_assignment";
  if (cat.includes("non-compete") || cat.includes("non_compete")) return "non_compete";
  if (cat.includes("renewal") || cat.includes("auto_renewal")) return "auto_renewal";
  if (cat.includes("liability") || cat.includes("limitation")) return "limitation_of_liability";
  if (cat.includes("termination")) return "termination";
  if (cat.includes("payment")) return "payment";
  if (cat.includes("governing")) return "governing_law";
  return "other";
}

export function useScan(jobId: string) {
  const { getToken } = useAuth();
  const api = useApiClient();
  const { addClause } = useClauseStore();
  const { updateProgress, setPowerResult, setSummaryResult, setComplete, setScanJob, status, contractId } = useScanStore();

  const onClause = useCallback((result: ClauseResult) => {
    const clause: Clause = {
      id: `${result.clause_index}-${Date.now()}`,
      contract_id: contractId || "",
      text: result.clause_text || "",
      position_index: result.clause_index || 0,
      risk_level: mapRiskLevel(result.risk_severity),
      risk_category: mapRiskCategory(result.risk_categories),
      plain_english: result.explanation || "",
      worst_case: result.recommendation || null,
      financial_exposure: null,
      negotiable: false,
      confidence: 0.85,
    };
    addClause(clause);
  }, [addClause, contractId]);

  const onProgress = useCallback((progressPct: number, step: string) => {
    updateProgress(progressPct);
  }, [updateProgress]);

  const onComplete = useCallback(async (summary: Record<string, unknown>) => {
    if (contractId) {
      try {
        const [power, summaryData] = await Promise.all([
          api.getPower(contractId),
          api.getSummary(contractId),
        ]);
        setPowerResult(power);
        setSummaryResult(summaryData);
      } catch (e) {
        console.error("Failed to fetch final data on complete:", e);
      }
    }
    setComplete();
  }, [contractId, api, setPowerResult, setSummaryResult, setComplete]);

  const onError = useCallback((error: string) => {
    console.error("SSE Error:", error);
  }, []);

  const { status: sseStatus, connect, disconnect } = useSSE({
    token: "",
    baseUrl: `${API_URL}/api`,
    onClause,
    onProgress,
    onComplete,
    onError,
  });

  const connectWithToken = useCallback(async () => {
    if (!jobId) return;
    try {
      const token = await getToken();
      if (!token) return;
      connect(jobId);
    } catch (e) {
      console.error("Failed to get token for SSE:", e);
    }
  }, [jobId, getToken, connect]);

  useEffect(() => {
    if (status !== "complete") {
      connectWithToken();
    }
    return () => {
      disconnect();
    };
  }, [status, connectWithToken, disconnect]);

  return { sseStatus };
}
