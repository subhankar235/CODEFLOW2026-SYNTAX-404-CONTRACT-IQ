export type ScanStatus = "queued" | "processing" | "complete" | "failed";

export interface ScanJob {
  id: string;
  contract_id: string;
  status: ScanStatus;
  progress_pct: number;
  created_at: string;
  completed_at: string | null;
  detected_language?: string | null;
}