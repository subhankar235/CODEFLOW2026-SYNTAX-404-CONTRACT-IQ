import { useAuth } from "@clerk/nextjs";
import { useCallback, useState } from "react";
import { ScanJob } from "@/types/scan";
import { Clause } from "@/types/clause";
import { AnalysisResult, PowerResult, SummaryResult, DashboardContract } from "@/types/analysis";
import { ChatMessage, CounterOffer, PrecedentMatch, Report, UploadResponse, ContractsResponse } from "@/types/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function useApiClient() {
  const { getToken } = useAuth();
  const [loading, setLoading] = useState(false);

  const request = useCallback(async <T,>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> => {
    setLoading(true);
    try {
      const token = await getToken();
      const response = await fetch(`${API_URL}${endpoint}`, {
        ...options,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
          ...options.headers,
        },
      });

      if (!response.ok) {
        if (response.status === 401) {
          window.location.href = "/sign-in";
          throw new Error("Unauthorized");
        }
      const body = await response.json().catch(() => ({}));
      const detail = body.detail;
      const message = typeof detail === "string" ? detail
        : Array.isArray(detail) ? detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join("; ")
        : `Request failed with status ${response.status}`;
      throw new Error(message);
      }

      return response.json();
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  const upload = useCallback((fileUrl: string, originalFilename: string, fileType: string, fileSize: number, encryptionKey?: string) => 
    request<UploadResponse>("/api/v1/upload", {
      method: "POST",
      body: JSON.stringify({ 
        file_url: fileUrl,
        original_filename: originalFilename,
        file_type: fileType,
        file_size_bytes: fileSize,
        encryption_key: encryptionKey
      }),
    }), [request]);

  const getContracts = useCallback(() => 
    request<ContractsResponse>("/api/v1/contracts/"), [request]);

  const getScanJob = useCallback((jobId: string) => 
    request<ScanJob>(`/api/v1/scan/${jobId}`), [request]);

  const triggerProcess = useCallback((jobId: string) => 
    request<{status: string}>(`/api/v1/upload/process/${jobId}`, { method: "POST" }), [request]);

  const getClauses = useCallback((contractId: string) => 
    request<Clause[]>(`/api/v1/contracts/${contractId}/clauses`), [request]);

  const getSummary = useCallback(async (contractId: string) => {
    const response = await request<{ summary: SummaryResult }>(`/api/v1/summary/${contractId}`);
    return response.summary;
  }, [request]);

  const getAnalysis = useCallback(async (contractId: string) => {
    const response = await request<any>(`/api/v1/contracts/${contractId}`);
    return response.analysis_result as AnalysisResult;
  }, [request]);

  const getPower = useCallback((contractId: string) => 
    request<PowerResult>(`/api/v1/power/${contractId}`), [request]);

  const getPrecedent = useCallback((clauseId: string) => 
    request<PrecedentMatch>(`/api/v1/precedent/${clauseId}`), [request]);

  const generateCounterOffer = useCallback((clauseId: string) => 
    request<{ task_id: string }>(`/api/v1/counter-offer/${clauseId}`, { method: "POST" }), [request]);

  const getCounterOffer = useCallback((clauseId: string) => 
    request<CounterOffer>(`/api/v1/counter-offer/${clauseId}`), [request]);

  const generateReport = useCallback((contractId: string) => 
    request<{ report_id: string }>(`/api/v1/report/generate/${contractId}`, { method: "POST" }), [request]);

  const getReport = useCallback((reportId: string) => 
    request<Report>(`/api/v1/report/${reportId}`), [request]);

  const getSharedReport = useCallback((shareUuid: string) => 
    request<Report>(`/api/v1/report/share/${shareUuid}`), [request]);

  const chat = useCallback((contractId: string, message: string, conversationId?: string) =>
    request<ChatMessage>(`/api/v1/chat/${contractId}`, {
      method: "POST",
      body: JSON.stringify({ message, conversation_id: conversationId }),
    }), [request]);

  const translate = useCallback((contractId: string, targetLanguage: string) =>
    request<{ task_id: string }>(`/api/v1/translate/${contractId}`, {
      method: "POST",
      body: JSON.stringify({ target_language: targetLanguage }),
    }), [request]);

  const getDashboard = useCallback(() =>
    request<{
      contracts: DashboardContract[];
      power_trend: { average_power_score: number; trend_description: string } | null;
    }>("/api/v1/dashboard"), [request]);

  return {
    loading,
    upload,
    getContracts,
    getScanJob,
    triggerProcess,
    getClauses,
    getAnalysis,
    getSummary,
    getPower,
    getPrecedent,
    generateCounterOffer,
    getCounterOffer,
    generateReport,
    getReport,
    getSharedReport,
    chat,
    translate,
    getDashboard,
  };
}