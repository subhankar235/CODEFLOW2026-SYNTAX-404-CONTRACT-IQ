"""
Tests for Step 6.2 — Risk Mapper (Triage Logic).
"""

import pytest

from services.ai.app.rules.risk_mapper import (
    TriageLevel,
    RiskMapperResult,
    ClauseTriage,
    map_clause_risk,
    triage_clauses,
    partition_by_triage,
)


class TestTriageLevelEnum:
    def test_green_level(self):
        assert TriageLevel.GREEN.value == "GREEN"

    def test_yellow_level(self):
        assert TriageLevel.YELLOW.value == "YELLOW"

    def test_red_level(self):
        assert TriageLevel.RED.value == "RED"


class TestMapClauseRisk:
    def test_no_signals_returns_green(self):
        text = "This is a standard provision with no unusual terms."
        result = map_clause_risk(text)
        assert result.triage == TriageLevel.GREEN
        assert result.match_count == 0

    def test_indemnity_hits_red(self):
        text = "The party shall indemnify and hold harmless the other party from any and all claims."
        result = map_clause_risk(text)
        assert result.triage == TriageLevel.RED
        assert "indemnity" in result.categories

    def test_ip_assignment_hits_red(self):
        text = "Employee agrees that all intellectual property created during employment belongs to Employer."
        result = map_clause_risk(text)
        assert result.triage == TriageLevel.RED
        assert "ip_assignment" in result.categories

    def test_auto_renewal_hits_yellow(self):
        text = "The agreement shall automatically renew for successive one-year terms unless written notice is given."
        result = map_clause_risk(text)
        assert result.triage == TriageLevel.YELLOW
        assert result.match_count >= 1
        assert "auto_renewal" in result.categories

    def test_single_medium_risk_hits_yellow(self):
        text = "The agreement shall automatically renew each year unless written notice is given."
        result = map_clause_risk(text)
        assert result.triage == TriageLevel.YELLOW
        assert result.match_count >= 1

    def test_two_medium_risks_hits_yellow(self):
        text = "The agreement shall automatically renew. Total liability shall not exceed fees paid."
        result = map_clause_risk(text)
        assert result.triage == TriageLevel.YELLOW
        assert result.match_count == 2

    def test_multiple_medium_risks(self):
        text = "The agreement shall automatically renew. Total liability shall not exceed fees paid. Governing law is Delaware."
        result = map_clause_risk(text)
        assert result.match_count >= 2

    def test_any_high_risk_hits_red(self):
        text = "Employee shall not engage in any competing business for 12 months worldwide."
        result = map_clause_risk(text)
        assert result.triage == TriageLevel.RED
        assert result.preliminary_risk_level == "HIGH"

    def test_empty_clause_returns_green(self):
        text = ""
        result = map_clause_risk(text)
        assert result.triage == TriageLevel.GREEN

    def test_whitespace_clause_returns_green(self):
        text = "   "
        result = map_clause_risk(text)
        assert result.triage == TriageLevel.GREEN


class TestRiskMapperResult:
    def test_categories_property(self):
        text = "The party shall indemnify and hold harmless."
        result = map_clause_risk(text)
        assert "indemnity" in result.categories

    def test_preliminary_risk_level_high_when_high_hit(self):
        text = "Employee shall not engage in any competing business for 12 months anywhere."
        result = map_clause_risk(text)
        assert result.preliminary_risk_level == "HIGH"

    def test_preliminary_risk_level_medium_when_only_medium_hits(self):
        text = "The agreement shall automatically renew each year unless written notice is given."
        result = map_clause_risk(text)
        assert result.preliminary_risk_level == "MEDIUM"

    def test_preliminary_risk_level_none_when_green(self):
        text = "Standard provision."
        result = map_clause_risk(text)
        assert result.preliminary_risk_level is None

    def test_to_dict_method(self):
        text = "Indemnify and hold harmless."
        result = map_clause_risk(text)
        d = result.to_dict()
        assert "triage" in d
        assert "match_count" in d
        assert "categories" in d


class TestTriageClauses:
    def test_returns_list_of_clause_triage(self):
        clauses = [
            "Standard provision.",
            "The party shall indemnify.",
            "Auto renewal applies.",
        ]
        results = triage_clauses(clauses)
        assert len(results) == 3
        assert all(isinstance(r, ClauseTriage) for r in results)

    def test_maintains_order(self):
        clauses = ["First clause.", "Second clause.", "Third clause."]
        results = triage_clauses(clauses)
        assert results[0].index == 0
        assert results[1].index == 1
        assert results[2].index == 2

    def test_clause_text_preserved(self):
        clause_text = "This is the clause text."
        results = triage_clauses([clause_text])
        assert results[0].text == clause_text


class TestPartitionByTriage:
    def test_all_green(self):
        clauses = ["A", "B", "C"]
        results = triage_clauses(clauses)
        partitioned = partition_by_triage(results)
        assert len(partitioned["GREEN"]) == 3
        assert len(partitioned["YELLOW"]) == 0
        assert len(partitioned["RED"]) == 0

    def test_mixed_triage(self):
        clauses = [
            "Standard clause.",
            "Employee shall indemnify and hold harmless.",
            "The agreement shall automatically renew.",
            "Employee shall not engage in any competing business.",
        ]
        results = triage_clauses(clauses)
        partitioned = partition_by_triage(results)
        assert len(partitioned["GREEN"]) == 1
        assert len(partitioned["YELLOW"]) == 1
        assert len(partitioned["RED"]) == 2

    def test_returns_correct_keys(self):
        clauses = ["Standard."]
        results = triage_clauses(clauses)
        partitioned = partition_by_triage(results)
        assert "GREEN" in partitioned
        assert "YELLOW" in partitioned
        assert "RED" in partitioned


class TestTriageRulesFromPRD:
    def test_indemnity_triggers_red(self):
        clause = "The party shall indemnify and hold harmless the other party."
        result = map_clause_risk(clause)
        assert result.triage == TriageLevel.RED

    def test_ip_assignment_triggers_red(self):
        clause = "Employee agrees that all intellectual property created belongs to Company."
        result = map_clause_risk(clause)
        assert result.triage == TriageLevel.RED

    def test_auto_renewal_triggers_yellow_or_red(self):
        clause = "The agreement shall automatically renew for successive terms."
        result = map_clause_risk(clause)
        assert result.triage in [TriageLevel.YELLOW, TriageLevel.RED]

    def test_no_risk_signals_triaged_green(self):
        clause = "This agreement is entered into as of January 1, 2024."
        result = map_clause_risk(clause)
        assert result.triage == TriageLevel.GREEN

    def test_one_signal_triaged_yellow(self):
        clause = "The agreement shall automatically renew each year unless written notice is given."
        result = map_clause_risk(clause)
        assert result.triage == TriageLevel.YELLOW

    def test_high_level_immediately_red(self):
        clause = "Employee shall not engage in any competing business for 12 months."
        result = map_clause_risk(clause)
        assert result.triage == TriageLevel.RED


class TestClauseTriage:
    def test_has_index(self):
        clauses = ["First", "Second"]
        results = triage_clauses(clauses)
        assert results[0].index == 0
        assert results[1].index == 1

    def test_has_text(self):
        text = "Test clause text"
        results = triage_clauses([text])
        assert results[0].text == text

    def test_has_result(self):
        text = "Standard clause"
        results = triage_clauses([text])
        assert hasattr(results[0], "result")
        assert isinstance(results[0].result, RiskMapperResult)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])