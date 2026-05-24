import { Clause, ConsequenceData } from "./clause";

export type ShouldSign = "yes_as-is" | "yes_with_changes" | "no";
export type NegotiatingPower = "Strong" | "Moderate" | "Weak";

export interface AnalysisResult {
  id: string;
  contract_id: string;
  overall_risk_score: number;
  should_sign: ShouldSign;
  top_concerns: string[];
  top_positives: string[];
  negotiating_power: NegotiatingPower;
  created_at: string;
}

export interface PowerResult {
  id: string;
  contract_id: string;
  power_score: number;
  power_label: string;
  key_imbalances: {
    clause: string;
    why: string;
    score: number;
  }[];
  leverage_points: string[];
}

export interface SummaryResult {
  one_liner: string;
  should_you_sign: ShouldSign;
  top_3_concerns: string[];
  top_2_positives: string[];
  overall_risk_score: number;
  negotiating_power: NegotiatingPower;
  contract_type?: string;
}

export interface ConsequenceResult {
  headline: string;
  scenario: string;
  financial_exposure: string | null;
  probability: "Low" | "Medium" | "High";
  similar_case: string | null;
  negotiable: boolean;
}

export interface PowerTrend {
  average_power_score: number;
  trend_description: string;
}

export interface DashboardContract {
  id: string;
  file_name: string;
  contract_type: string;
  overall_risk_score: number;
  should_sign: ShouldSign;
  created_at: string;
  status: "processing" | "complete";
}