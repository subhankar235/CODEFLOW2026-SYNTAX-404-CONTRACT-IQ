import { create } from "zustand";
import { persist } from "zustand/middleware";

interface ReportState {
  reportId: string | null;
  shareUuid: string | null;
  status: "idle" | "generating" | "ready";
  expiresAt: string | null;
  setGenerating: () => void;
  setReady: (reportId: string, shareUuid: string, expiresAt: string) => void;
  reset: () => void;
}

export const useReportStore = create<ReportState>()(
  persist(
    (set) => ({
      reportId: null,
      shareUuid: null,
      status: "idle",
      expiresAt: null,
      setGenerating: () => set({ status: "generating" }),
      setReady: (reportId, shareUuid, expiresAt) =>
        set({ reportId, shareUuid, status: "ready", expiresAt }),
      reset: () =>
        set({
          reportId: null,
          shareUuid: null,
          status: "idle",
          expiresAt: null,
        }),
    }),
    {
      name: "report-store",
      partialize: (state) => ({
        reportId: state.reportId,
        shareUuid: state.shareUuid,
      }),
    }
  )
);