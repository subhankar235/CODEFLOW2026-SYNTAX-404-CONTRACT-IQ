"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { useScanStore } from "@/store/scanStore";
import { useClauseStore } from "@/store/clauseStore";
import { useLanguageStore, LANGUAGE_NAMES } from "@/store/languageStore";
import { useUIStore } from "@/store/uiStore";
import { useApiClient } from "@/lib/api";
import { useSSE, ClauseResult } from "@/hooks/useSSE";
import { ClauseList } from "@/features/analysis/ClauseList";
import { ConsequencePanel } from "@/features/analysis/ConsequencePanel";
import { PowerMeter } from "@/features/power/PowerMeter";
import { SummaryCard, SummaryCardSkeleton } from "@/features/summary/SummaryCard";
import { ProsConsSnapshot } from "@/features/summary/ProsConsSnapshot";
import { LanguageDetectionBanner } from "@/features/multilingual/LanguageDetectionBanner";
import { BilingualToggle } from "@/features/multilingual/BilingualToggle";
import { Loader2, MessageSquare, ShieldCheck, X } from "lucide-react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { Clause, RiskLevel, RiskCategory } from "@/types/clause";

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

export default function ScanPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const jobId = params.jobId as string;
  // Read clause deep-link from URL (set by ClauseCitation pill in chat)
  const deepLinkedClauseId = searchParams.get("clause");

  const { getToken } = useAuth();
  const api = useApiClient();
  const { clauses, selectedClauseId } = useClauseStore();
  const {
    status,
    powerResult,
    summaryResult,
    updateProgress,
    setComplete,
    contractId,
  } = useScanStore();

  const { setDetectedLanguage, reset: resetLanguage } = useLanguageStore();
  const { resetLanguageBanner } = useUIStore();

  const [initialLoading, setInitialLoading] = useState(true);
  const [mobilePanelOpen, setMobilePanelOpen] = useState(false);
  const [sseToken, setSseToken] = useState<string>("");
  const dataLoadedRef = useRef(false);

  const sse = useSSE({
    token: sseToken,
    baseUrl: `${API_URL}/api`,
    onClause: useCallback((result: any) => {
      const clause: Clause = {
        id: result.clause_id || `${result.position_index}-${Date.now()}-${Math.random().toString(36).slice(2)}`,
        contract_id: contractId || "",
        text: result.text || "",
        position_index: result.position_index || 0,
        risk_level: mapRiskLevel(result.risk_level || "LOW"),
        risk_category: mapRiskCategory(result.risk_categories || []),
        plain_english: result.plain_english || "",
        worst_case: result.worst_case_scenario || null,
        financial_exposure: result.financial_exposure || null,
        negotiable: result.negotiable ?? false,
        confidence: result.confidence ?? 0.85,
        headline: result.headline || null,
        scenario: result.scenario || null,
        probability: (result.probability as "Low" | "Medium" | "High") || undefined,
        similar_case: result.similar_case || null,
      };
      useClauseStore.getState().addClause(clause);
    }, [contractId]),
    onProgress: useCallback((pct: number) => {
      updateProgress(pct);
    }, [updateProgress]),
    onComplete: useCallback(async () => {
      if (contractId) {
        try {
          const [power, summaryData, finalClauses] = await Promise.all([
            api.getPower(contractId),
            api.getSummary(contractId),
            api.getClauses(contractId).catch(() => null),
          ]);
          if (power) useScanStore.getState().setPowerResult(power);
          if (summaryData) useScanStore.getState().setSummaryResult(summaryData);
          if (finalClauses && finalClauses.length > 0) {
            useClauseStore.getState().setClauses(finalClauses);
          }
        } catch (e) {
          console.error("Failed to fetch final data on complete:", e);
        }
      }
      setComplete();
    }, [contractId, api, setComplete]),
    onError: useCallback((error: string) => {
      console.error("SSE Error:", error);
    }, []),
  });

  // Reset language state whenever we load a new job
  useEffect(() => {
    resetLanguage();
    resetLanguageBanner();
    useClauseStore.getState().reset();
    dataLoadedRef.current = false;
  }, [jobId, resetLanguage, resetLanguageBanner]);

  useEffect(() => {
    if (!jobId) return;

    async function loadData() {
      if (dataLoadedRef.current) return;

      try {
        const job = await api.getScanJob(jobId);
        useScanStore.getState().setScanJob(job.id, job.contract_id);

        // Set detected language from contract data
        if (job.detected_language) {
          const langCode = job.detected_language.toLowerCase();
          const langName = LANGUAGE_NAMES[langCode] || null;
          setDetectedLanguage(langCode, langName);
        }

        if (job.status === "complete") {
          try {
            const fetchedClauses = await api.getClauses(job.contract_id);
            if (fetchedClauses && fetchedClauses.length > 0) {
              useClauseStore.getState().setClauses(fetchedClauses);
            }
            dataLoadedRef.current = true;
          } catch (clauseErr) {
            console.error("Failed to fetch clauses:", clauseErr);
            dataLoadedRef.current = true;
          }

          try {
            const [power, summaryData] = await Promise.all([
              api.getPower(job.contract_id),
              api.getSummary(job.contract_id),
            ]);
            if (power) useScanStore.getState().setPowerResult(power);
            if (summaryData) useScanStore.getState().setSummaryResult(summaryData);
          } catch {
            // Power/summary are optional
          }
          useScanStore.getState().setComplete();
        } else if (job.status === "processing" || job.status === "queued") {
          const userToken = await getToken();
          if (userToken) {
            setSseToken(userToken);
          }
        }
      } catch (err) {
        console.error("Error loading scan data:", err);
        dataLoadedRef.current = true;
        useScanStore.getState().setFailed("Failed to load scan data");
      } finally {
        setInitialLoading(false);
      }
    }
    loadData();
  }, [jobId, getToken, setDetectedLanguage]);

  // Auto-select clause from deep-link URL param (from ClauseCitation pill)
  useEffect(() => {
    if (deepLinkedClauseId && clauses.length > 0) {
      const matched = clauses.find((c) => c.id === deepLinkedClauseId);
      if (matched) {
        useClauseStore.getState().selectClause(deepLinkedClauseId);
        // On mobile, open the panel automatically
        setMobilePanelOpen(true);
      }
    }
  }, [deepLinkedClauseId, clauses]);

  useEffect(() => {
    if (!sseToken || status === "complete" || !jobId) return;
    sse.connect(jobId, sseToken);
    return () => {
      sse.disconnect();
    };
  }, [sseToken, status, jobId]);

  const selectedClause = clauses.find((c) => c.id === selectedClauseId);

  const openMobilePanel = (clauseId: string) => {
    useClauseStore.getState().selectClause(clauseId);
    setMobilePanelOpen(true);
  };

  const closeMobilePanel = () => {
    setMobilePanelOpen(false);
  };

  if (initialLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  const showSummaryCard = status === "complete" && summaryResult;
  const showProsCons = status === "complete" && summaryResult;
  const showPowerMeter = status === "complete" && powerResult;

  return (
    <div className="flex flex-col h-full min-h-0 overflow-hidden container mx-auto py-4 md:py-6 px-4 gap-4 md:gap-6">
      {/* Header bar */}
      <div className="flex items-center justify-between border-b pb-4 shrink-0">
        <div className="flex items-center gap-3">
          <div className="hidden md:flex h-10 w-10 rounded-xl bg-primary/10 items-center justify-center">
            <ShieldCheck className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-lg md:text-xl font-bold tracking-tight">Contract Analysis</h1>
            <p className="text-xs text-muted-foreground uppercase tracking-widest font-semibold">
              {status === "complete" ? "Scan Complete" : "Integrity Scan In Progress"}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Bilingual toggle — shows only if non-English contract detected */}
          {contractId && (
            <BilingualToggle contractId={contractId} />
          )}

          <Link
            href={`/chat/${contractId || ""}?job=${jobId}`}
            className="flex items-center gap-2 rounded-lg bg-zinc-900 px-3 md:px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-800"
          >
            <MessageSquare className="h-4 w-4" />
            <span className="hidden sm:inline">Chat with AI</span>
          </Link>
        </div>
      </div>

      {/* Language detection banner */}
      {contractId && (
        <LanguageDetectionBanner contractId={contractId} />
      )}

      {showSummaryCard ? (
        <div className="shrink-0">
          <SummaryCard data={summaryResult!} />
        </div>
      ) : (
        status !== "complete" && (
          <div className="shrink-0">
            <SummaryCardSkeleton />
          </div>
        )
      )}

      <div className="flex-1 flex flex-col lg:flex-row gap-4 md:gap-6 min-h-0 overflow-hidden">
        <div className="w-full lg:w-[380px] xl:w-[440px] shrink-0 flex flex-col min-h-0 bg-background order-2 lg:order-1">
          <div className="flex items-center justify-between mb-4 shrink-0">
            <h2 className="text-lg font-bold tracking-tight">Contract Clauses</h2>
          </div>
          <div
            className="flex-1 min-h-0 relative"
            onClick={(e) => {
              const card = (e.target as HTMLElement).closest("[data-clause-id]");
              if (card) {
                openMobilePanel(card.getAttribute("data-clause-id")!);
              }
            }}
          >
            <ClauseList onCardClick={openMobilePanel} />
          </div>
        </div>

        <div className="flex-1 flex flex-col min-h-0 bg-card border rounded-xl shadow-sm overflow-hidden order-1 lg:order-2">
          <div className="flex-1 overflow-hidden">
            <AnimatePresence mode="wait">
              {selectedClause ? (
                <motion.div
                  key={selectedClause.id}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.2 }}
                  className="h-full"
                >
                  <ConsequencePanel clause={selectedClause} />
                </motion.div>
              ) : (
                <motion.div
                  key="empty"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex items-center justify-center h-full text-muted-foreground flex-col gap-4"
                >
                  <div className="h-16 w-16 rounded-full bg-muted flex items-center justify-center">
                    <span className="text-2xl opacity-50">📄</span>
                  </div>
                  <p className="text-sm text-center px-4">Select a clause from the list to see detailed analysis</p>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        <div className="w-full lg:w-[320px] xl:w-[360px] shrink-0 order-3 hidden lg:block">
          <div className="sticky top-0">
            {showPowerMeter ? (
              <PowerMeter />
            ) : (
              <div className="rounded-xl border bg-card p-8 shadow-sm">
                <div className="flex flex-col items-center justify-center space-y-6">
                  <div className="h-40 w-full max-w-[300px] animate-pulse rounded-t-full bg-muted/50" />
                  <div className="h-6 w-48 animate-pulse rounded bg-muted/50" />
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {showProsCons && summaryResult && (
        <div className="shrink-0">
          <ProsConsSnapshot
            topConcerns={summaryResult.top_3_concerns}
            topPositives={summaryResult.top_2_positives}
            verdict={summaryResult.one_liner}
          />
        </div>
      )}

      <AnimatePresence>
        {mobilePanelOpen && selectedClause && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/50 lg:hidden"
            onClick={closeMobilePanel}
          >
            <motion.div
              initial={{ y: "100%" }}
              animate={{ y: 0 }}
              exit={{ y: "100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 300 }}
              className="absolute bottom-0 left-0 right-0 max-h-[85vh] bg-card rounded-t-2xl shadow-xl overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between border-b p-4">
                <h3 className="font-semibold text-sm">Clause Details</h3>
                <button
                  onClick={closeMobilePanel}
                  className="p-1.5 rounded-full hover:bg-muted transition-colors"
                >
                  <X className="h-5 w-5 text-muted-foreground" />
                </button>
              </div>
              <div className="overflow-y-auto p-4 pb-8" style={{ maxHeight: "calc(85vh - 60px)" }}>
                <AnimatePresence mode="wait">
                  <motion.div
                    key={selectedClause.id}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    transition={{ duration: 0.2 }}
                  >
                    <ConsequencePanel clause={selectedClause} />
                  </motion.div>
                </AnimatePresence>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}