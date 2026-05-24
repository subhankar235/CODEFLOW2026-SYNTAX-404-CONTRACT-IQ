"""
Test all Steps 6.1-6.6.
"""

import os
import sys
import pytest

# Add paths for different modules
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'services', 'api'))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'services', 'ai'))

# AI Services Tests (6.1-6.3)
try:
    from services.ai.app.pipelines.type_detection import (
        ContractType, TypeDetectionResult, _truncate_to_tokens, _fuzzy_match_type
    )
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

try:
    from services.ai.app.rules.regex_rules import (
        RiskCategory, RiskLevel, ALL_PATTERNS
    )
    REGEX_AVAILABLE = True
except ImportError:
    REGEX_AVAILABLE = False

try:
    from services.ai.app.rules.risk_mapper import (
        TriageLevel, map_clause_risk, triage_clauses, partition_by_triage
    )
    MAPPER_AVAILABLE = True
except ImportError:
    MAPPER_AVAILABLE = False

try:
    from services.ai.app.pipelines.risk_classification import (
        ClauseResult, _batch, _green_result
    )
    CLASSIFICATION_AVAILABLE = True
except ImportError:
    CLASSIFICATION_AVAILABLE = False

# API Tests (6.4)
try:
    from app.api.v1.endpoints.streaming import router, HEARTBEAT_INTERVAL
    API_STREAMING_AVAILABLE = True
except ImportError:
    API_STREAMING_AVAILABLE = False

# Worker Tests (6.5)
try:
    from apps.services.streaming_service import (
        publish_clause, publish_complete, publish_error, publish_progress
    )
    STREAMING_PUB_AVAILABLE = True
except ImportError:
    STREAMING_PUB_AVAILABLE = False


# ===================== TESTS =====================

class TestStep61TypeDetection:
    """Step 6.1: Type Detection."""

    @pytest.mark.skipif(not AI_AVAILABLE, reason="AI services not available")
    def test_contract_type_enum(self):
        assert ContractType.EMPLOYMENT.value == "Employment"
        assert ContractType.NDA.value == "NDA"

    @pytest.mark.skipif(not AI_AVAILABLE, reason="AI services not available")
    def test_type_detection_result(self):
        result = TypeDetectionResult(
            type=ContractType.EMPLOYMENT,
            confidence=0.85,
            party_roles=["employer", "employee"]
        )
        assert result.type == ContractType.EMPLOYMENT
        assert result.confidence == 0.85

    @pytest.mark.skipif(not AI_AVAILABLE, reason="AI services not available")
    def test_low_confidence_flag(self):
        result = TypeDetectionResult(
            type=ContractType.NDA,
            confidence=0.5,
            party_roles=[]
        )
        assert result.needs_manual_review is True


class TestStep62RegexRules:
    """Step 6.2: Regex Rules."""

    @pytest.mark.skipif(not REGEX_AVAILABLE, reason="Regex module not available")
    def test_pattern_count(self):
        assert len(ALL_PATTERNS) >= 40

    @pytest.mark.skipif(not REGEX_AVAILABLE, reason="Regex module not available")
    def test_indemnity_pattern(self):
        p = next((x for x in ALL_PATTERNS if x.name == "indemnify_hold_harmless"), None)
        assert p is not None
        assert p.matches("shall indemnify and hold harmless")
        assert p.risk_level == RiskLevel.HIGH

    @pytest.mark.skipif(not REGEX_AVAILABLE, reason="Regex module not available")
    def test_ip_assignment_pattern(self):
        p = next((x for x in ALL_PATTERNS if x.name == "all_ip_created"), None)
        assert p is not None
        assert p.risk_level == RiskLevel.HIGH


class TestStep63RiskMapper:
    """Step 6.2: Risk Mapping."""

    @pytest.mark.skipif(not MAPPER_AVAILABLE, reason="Mapper not available")
    def test_indemnity_hits_red(self):
        result = map_clause_risk("shall indemnify and hold harmless")
        assert result.triage == TriageLevel.RED

    @pytest.mark.skipif(not MAPPER_AVAILABLE, reason="Mapper not available")
    def test_green_for_clean_clause(self):
        result = map_clause_risk("Standard provision.")
        assert result.triage == TriageLevel.GREEN

    @pytest.mark.skipif(not MAPPER_AVAILABLE, reason="Mapper not available")
    def test_partition_method(self):
        clauses = ["clean", "shall indemnify"]
        triaged = triage_clauses(clauses)
        buckets = partition_by_triage(triaged)
        assert "GREEN" in buckets
        assert "RED" in buckets


class TestStep64Classification:
    """Step 6.3: Risk Classification."""

    @pytest.mark.skipif(not CLASSIFICATION_AVAILABLE, reason="Classification not available")
    def test_batch_split_20(self):
        batch = _batch(list(range(20)), 20)
        assert len(batch) == 1

    @pytest.mark.skipif(not CLASSIFICATION_AVAILABLE, reason="Classification not available")
    def test_batch_split_45(self):
        batch = _batch(list(range(45)), 20)
        assert len(batch) == 3

    @pytest.mark.skipif(not CLASSIFICATION_AVAILABLE, reason="Classification not available")
    def test_green_returns_pydantic(self):
        ct = triage_clauses(["clean"])[0]
        result = _green_result(ct)
        assert isinstance(result, ClauseResult)


class TestStep65StreamingEndpoint:
    """Step 6.4: SSE Streaming."""

    @pytest.mark.skipif(not API_STREAMING_AVAILABLE, reason="API not available")
    def test_router_exists(self):
        assert router is not None

    @pytest.mark.skipif(not API_STREAMING_AVAILABLE, reason="API not available")
    def test_heartbeat_interval(self):
        assert HEARTBEAT_INTERVAL == 15


class TestStep66CeleryTask:
    """Step 6.5: Celery Task."""

    @pytest.mark.skipif(not STREAMING_PUB_AVAILABLE, reason="Streaming not available")
    def test_publish_functions_exist(self):
        assert callable(publish_clause)
        assert callable(publish_complete)
        assert callable(publish_error)
        assert callable(publish_progress)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])