export interface ApiError {
  status_code: number;
  detail: string;
}

export interface Contract {
  id: string;
  original_filename: string;
  file_type: string;
  detected_language: string;
  created_at: string;
}

export interface ContractsResponse {
  message: string;
  user_id: string;
  contracts: Contract[];
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  clause_citation: string | null;
  created_at: string;
}

export interface ApiResponse<T> {
  data?: T;
  error?: ApiError;
}

export interface UploadResponse {
  job_id: string;
  contract_id: string;
  status: string;
  progress_pct: number;
  error_message?: string;
}

export interface Report {
  id: string;
  contract_id: string;
  pdf_path: string;
  share_uuid: string;
  expires_at: string;
  language: string;
  created_at: string;
}

export interface CounterOffer {
  id: string;
  clause_id: string;
  aggressive_clause: string;
  balanced_clause: string;
  conservative_clause: string;
  explanation_aggressive: string;
  explanation_balanced: string;
  explanation_conservative: string;
  negotiation_email: string;
}

export interface PrecedentMatch {
  id: string;
  clause_id: string;
  precedent_summary: string;
  enforcement_likelihood: "Very Likely" | "Likely" | "Uncertain" | "Unlikely";
  confidence_score: number;
  cited_cases: {
    name: string;
    year: number;
    jurisdiction: string;
    outcome: string;
  }[];
}