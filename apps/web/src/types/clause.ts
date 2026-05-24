export type RiskLevel = "HIGH" | "MEDIUM" | "LOW" | "SAFE";

export type RiskCategory =
  | "indemnity"
  | "ip_assignment"
  | "non_compete"
  | "auto_renewal"
  | "limitation_of_liability"
  | "termination"
  | "payment"
  | "governing_law"
  | "other";

export type ContractType =
  | "employment"
  | "nda"
  | "freelance"
  | "saas"
  | "lease"
  | "partnership"
  | "ip_license"
  | "loan"
  | "m&a"
  | "other";

export interface Clause {
  id: string;
  contract_id: string;
  text: string;
  position_index: number;
  risk_level: RiskLevel;
  risk_category: RiskCategory;
  plain_english: string;
  worst_case: string | null;
  financial_exposure: string | null;
  negotiable: boolean;
  confidence: number;
  headline?: string | null;
  scenario?: string | null;
  probability?: "Low" | "Medium" | "High" | null;
  similar_case?: string | null;
  // Translated fields (populated after translation)
  plain_english_translated?: string | null;
  worst_case_translated?: string | null;
  headline_translated?: string | null;
  scenario_translated?: string | null;
  text_translated?: string | null;
}

export interface ConsequenceData {
  headline: string;
  scenario: string;
  financial_exposure: string;
  probability: "Low" | "Medium" | "High";
  similar_case: string | null;
}