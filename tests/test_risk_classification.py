"""
Tests for Step 6.3 — Risk Classification Pipeline.
"""

import pytest

from services.ai.app.pipelines.risk_classification import (
    RiskSeverity,
    SafetyRating,
    ClauseResult,
    run_risk_classification,
    stream_risk_classification,
    async_stream_risk_classification,
    _batch,
    _parse_llm_response,
    _build_user_message,
    _green_result,
    _fallback_single,
    PRIMARY_MODEL,
    MAX_BATCH_SIZE,
)
from services.ai.app.rules.risk_mapper import (
    ClauseTriage,
    TriageLevel,
    map_clause_risk,
)


class TestRiskSeverityEnum:
    def test_all_levels_present(self):
        assert RiskSeverity.LOW.value == "LOW"
        assert RiskSeverity.MEDIUM.value == "MEDIUM"
        assert RiskSeverity.HIGH.value == "HIGH"
        assert RiskSeverity.CRITICAL.value == "CRITICAL"


class TestSafetyRatingEnum:
    def test_all_ratings_present(self):
        assert SafetyRating.SAFE.value == "SAFE"
        assert SafetyRating.CAUTION.value == "CAUTION"
        assert SafetyRating.DANGER.value == "DANGER"


class TestClauseResult:
    def test_valid_clause_result(self):
        result = ClauseResult(
            clause_index=0,
            clause_text="Sample clause text",
            triage="GREEN",
            risk_severity=RiskSeverity.LOW,
            safety_rating=SafetyRating.SAFE,
            risk_categories=[],
        )
        assert result.clause_index == 0
        assert result.llm_analysed is False

    def test_returns_pydantic_not_dict(self):
        result = ClauseResult(
            clause_index=0,
            clause_text="text",
            triage="GREEN",
        )
        assert isinstance(result, ClauseResult)
        assert not isinstance(result, dict)

    def test_llm_analysed_flag(self):
        result = ClauseResult(
            clause_index=0,
            clause_text="text",
            triage="YELLOW",
            llm_analysed=True,
        )
        assert result.llm_analysed is True


class TestBatchSplitter:
    def test_single_batch(self):
        items = list(range(5))
        batches = _batch(items, 20)
        assert len(batches) == 1
        assert batches[0] == items

    def test_exact_batch_size(self):
        items = list(range(20))
        batches = _batch(items, 20)
        assert len(batches) == 1
        assert len(batches[0]) == 20

    def test_multiple_batches(self):
        items = list(range(45))
        batches = _batch(items, 20)
        assert len(batches) == 3
        assert len(batches[0]) == 20
        assert len(batches[1]) == 20
        assert len(batches[2]) == 5

    def test_empty_list(self):
        items = []
        batches = _batch(items, 20)
        assert len(batches) == 0


class TestGreenResult:
    def test_green_returns_safe(self):
        ct = ClauseTriage(index=0, text="Standard clause", result=map_clause_risk("Standard clause"))
        result = _green_result(ct)
        assert result.triage == "GREEN"
        assert result.risk_severity == RiskSeverity.LOW
        assert result.safety_rating == SafetyRating.SAFE
        assert result.llm_analysed is False


class TestFallbackResult:
    def test_yellow_becomes_medium_caution(self):
        ct = ClauseTriage(index=0, text="Some clause", result=map_clause_risk("auto renew clause"))
        result = _fallback_single(ct)
        assert result.risk_severity == RiskSeverity.MEDIUM
        assert result.safety_rating == SafetyRating.CAUTION

    def test_red_becomes_high_danger(self):
        ct = ClauseTriage(index=0, text="Some clause", result=map_clause_risk("shall indemnify"))
        result = _fallback_single(ct)
        assert result.risk_severity == RiskSeverity.HIGH
        assert result.safety_rating == SafetyRating.DANGER


class TestBuildUserMessage:
    def test_includes_contract_type(self):
        ct = ClauseTriage(index=0, text="clause", result=map_clause_risk("clause"))
        msg = _build_user_message([ct], "Employment", "employee")
        assert "Employment" in msg

    def test_includes_user_role(self):
        ct = ClauseTriage(index=0, text="clause", result=map_clause_risk("clause"))
        msg = _build_user_message([ct], "Employment", "employee")
        assert "employee" in msg

    def test_includes_clauses(self):
        ct = ClauseTriage(index=0, text="The clause text", result=map_clause_risk("The clause text"))
        msg = _build_user_message([ct], "NDA", "client")
        assert "The clause text" in msg


class TestParseLLMResponse:
    def test_valid_response_parsed(self):
        ct = ClauseTriage(index=0, text="clause", result=map_clause_risk("clause"))
        raw = '[{"index": 0, "risk_severity": "HIGH", "safety_rating": "DANGER", "risk_categories": ["liability"], "explanation": "High risk", "recommendation": "Review"}]'
        results = _parse_llm_response(raw, [ct], "Employment")
        assert len(results) == 1
        assert results[0].risk_severity == RiskSeverity.HIGH
        assert results[0].safety_rating == SafetyRating.DANGER

    def test_json_with_markdown_fence(self):
        ct = ClauseTriage(index=0, text="clause", result=map_clause_risk("clause"))
        raw = '```json\n[{"index": 0, "risk_severity": "MEDIUM", "safety_rating": "CAUTION", "risk_categories": [], "explanation": "test", "recommendation": "test"}]\n```'
        results = _parse_llm_response(raw, [ct], "NDA")
        assert len(results) == 1

    def test_invalid_json_falls_back(self):
        ct = ClauseTriage(index=0, text="clause", result=map_clause_risk("clause"))
        raw = "not valid json"
        results = _parse_llm_response(raw, [ct], "NDA")
        assert len(results) == 1
        assert results[0].llm_analysed is False


class TestConstants:
    def test_max_batch_size_is_20(self):
        assert MAX_BATCH_SIZE == 20


class TestFunctionSignatures:
    def test_run_risk_classification_exists(self):
        import inspect
        sig = inspect.signature(run_risk_classification)
        assert "clauses" in sig.parameters

    def test_stream_risk_classification_exists(self):
        import inspect
        sig = inspect.signature(stream_risk_classification)
        assert "clauses" in sig.parameters

    def test_async_stream_exists(self):
        import inspect
        sig = inspect.signature(async_stream_risk_classification)
        assert "clauses" in sig.parameters


class TestPydanticValidation:
    def test_valid_pydantic_output(self):
        ct = ClauseTriage(index=0, text="clause", result=map_clause_risk("clause"))
        result = _green_result(ct)
        assert isinstance(result, ClauseResult)

    def test_triage_accepts_string_values(self):
        result = ClauseResult(
            clause_index=0,
            clause_text="text",
            triage="GREEN",
        )
        assert result.triage == "GREEN"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])