import { create } from "zustand";
import { persist } from "zustand/middleware";
import { ScanStatus } from "@/types/scan";
import { PowerResult, SummaryResult } from "@/types/analysis";

interface ScanState {
  jobId: string | null;
  contractId: string | null;
  status: ScanStatus;
  progressPct: number;
  error: string | null;
  powerResult: PowerResult | null;
  summaryResult: SummaryResult | null;
  setScanJob: (jobId: string, contractId: string) => void;
  updateProgress: (progressPct: number, status?: ScanStatus) => void;
  setPowerResult: (powerResult: PowerResult) => void;
  setSummaryResult: (summaryResult: SummaryResult) => void;
  setComplete: () => void;
  setFailed: (error: string) => void;
  reset: () => void;
}

export const useScanStore = create<ScanState>()(
  persist(
    (set) => ({
      jobId: null,
      contractId: null,
      status: "queued",
      progressPct: 0,
      error: null,
      powerResult: null,
      summaryResult: null,
      setScanJob: (jobId, contractId) =>
        set({ jobId, contractId, status: "queued", progressPct: 0, error: null, powerResult: null, summaryResult: null }),
      updateProgress: (progressPct, status) =>
        set((state) => ({
          progressPct,
          status: status || state.status,
        })),
      setPowerResult: (powerResult) => set({ powerResult }),
      setSummaryResult: (summaryResult) => set({ summaryResult }),
      setComplete: () => set({ status: "complete", progressPct: 100 }),
      setFailed: (error) => set({ status: "failed", error }),
      reset: () =>
        set({
          jobId: null,
          contractId: null,
          status: "queued",
          progressPct: 0,
          error: null,
          powerResult: null,
          summaryResult: null,
        }),
    }),
    {
      name: "scan-store",
      partialize: (state) => ({
        jobId: state.jobId,
        contractId: state.contractId,
      }),
    }
  )
);