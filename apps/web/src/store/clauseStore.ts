import { create } from "zustand";
import { Clause, RiskLevel } from "@/types/clause";

interface ClauseState {
  clauses: Clause[];
  selectedClauseId: string | null;
  filter: RiskLevel | "ALL";
  addClause: (clause: Clause) => void;
  setClauses: (clauses: Clause[]) => void;
  selectClause: (clauseId: string | null) => void;
  setFilter: (filter: RiskLevel | "ALL") => void;
  // Merge translated fields into existing clauses by ID
  setTranslatedClauses: (translatedClauses: Partial<Clause>[]) => void;
  reset: () => void;
}

export const useClauseStore = create<ClauseState>()((set) => ({
  clauses: [],
  selectedClauseId: null,
  filter: "ALL",
  addClause: (clause) =>
    set((state) => {
      // Check if clause already exists by id or position_index
      const exists = state.clauses.findIndex(
        (c) => c.id === clause.id || c.position_index === clause.position_index
      );
      if (exists >= 0) {
        const newClauses = [...state.clauses];
        newClauses[exists] = clause;
        return { clauses: newClauses };
      }
      return { clauses: [...state.clauses, clause] };
    }),
  setClauses: (clauses) => set({ clauses }),
  selectClause: (clauseId) => set({ selectedClauseId: clauseId }),
  setFilter: (filter) => set({ filter }),
  setTranslatedClauses: (translatedClauses) =>
    set((state) => ({
      clauses: state.clauses.map((clause) => {
        const translated = translatedClauses.find((tc) => tc.id === clause.id);
        if (!translated) return clause;
        return {
          ...clause,
          plain_english_translated: translated.plain_english_translated ?? clause.plain_english_translated,
          worst_case_translated: translated.worst_case_translated ?? clause.worst_case_translated,
          headline_translated: translated.headline_translated ?? clause.headline_translated,
          scenario_translated: translated.scenario_translated ?? clause.scenario_translated,
          text_translated: translated.text_translated ?? clause.text_translated,
        };
      }),
    })),
  reset: () => set({ clauses: [], selectedClauseId: null, filter: "ALL" }),
}));