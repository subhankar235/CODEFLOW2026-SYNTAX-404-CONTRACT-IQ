"""
Tests for Pydantic schemas.
"""

import pytest
from pydantic import ValidationError

from services.api.app.schemas import (
    RiskLevel,
    ContractType,
    ClauseResult,
    ContractCreate,
    ScanRequest,
    ScanStatus,
    ImpactSeverity,
    Likelihood,
    NegotiationPriority,
    AcceptanceLikelihood,
    AsymmetryCategory,
    Enforceability,
    PrecedentType,
)

from services.ai.schemas.llm_responses import (
    LLMRiskAnalysis,
    LLMTypeDetection,
    LLMConsequence,
    LLMSummary,
    LLMPowerAsymmetry,
    LLMCounterOffer,
    LLMPrecedent,
)
from services.ai.schemas.validate_llm_response import (
    validate_llm_response,
    validate_risk_analysis,
    validate_type_detection,
    validate_consequence,
    validate_summary,
    validate_power_asymmetry,
    validate_counter_offer,
    validate_precedent,
)


class TestEnums:
    """Test enum values match PRD.md."""

    def test_risk_level_values(self):
        assert RiskLevel.CRITICAL.value == "CRITICAL"
        assert RiskLevel.HIGH.value == "HIGH"
        assert RiskLevel.MEDIUM.value == "MEDIUM"
        assert RiskLevel.LOW.value == "LOW"
        assert RiskLevel.NONE.value == "NONE"

    def test_contract_type_values(self):
        assert ContractType.NDA.value == "NDA"
        assert ContractType.EMPLOYMENT.value == "Employment Agreement"
        assert ContractType.SERVICE.value == "Service Agreement"

    def test_impact_severity_values(self):
        assert ImpactSeverity.CATASTROPHIC.value == "CATASTROPHIC"
        assert ImpactSeverity.SEVERE.value == "SEVERE"

    def test_likelihood_values(self):
        assert Likelihood.CERTAIN.value == "CERTAIN"
        assert Likelihood.LIKELY.value == "LIKELY"


class TestClauseResult:
    """Test ClauseResult validation."""

    def test_valid_clause_result(self):
        data = {
            "clause_id": "550e8400-e29b-41d4-a716-446655440000",
            "position_index": 0,
            "text": "Test clause text",
            "risk_level": "HIGH",
            "risk_category": "liability",
            "risk_summary": "High liability exposure",
            "risk_explanation": "This clause exposes the party to unlimited liability.",
            "problematic_language": "unlimited liability",
            "recommendations": [{"text": "Add liability cap"}],
            "confidence_score": 0.9,
        }
        result = ClauseResult.model_validate(data)
        assert result.risk_level == RiskLevel.HIGH
        assert result.position_index == 0
        assert result.confidence_score == 0.9

    def test_missing_required_field_raises(self):
        data = {
            "clause_id": "550e8400-e29b-41d4-a716-446655440000",
            "position_index": 0,
            "text": "Test clause",
            # Missing: risk_level, risk_category, risk_summary, etc.
        }
        with pytest.raises(ValidationError):
            ClauseResult.model_validate(data)

    def test_invalid_risk_level_raises(self):
        data = {
            "clause_id": "550e8400-e29b-41d4-a716-446655440000",
            "position_index": 0,
            "text": "Test clause",
            "risk_level": "INVALID",
            "risk_category": "test",
            "risk_summary": "test",
            "risk_explanation": "test",
            "confidence_score": 0.9,
        }
        with pytest.raises(ValidationError):
            ClauseResult.model_validate(data)

    def test_confidence_score_out_of_range(self):
        data = {
            "clause_id": "550e8400-e29b-41d4-a716-446655440000",
            "position_index": 0,
            "text": "Test clause",
            "risk_level": "LOW",
            "risk_category": "test",
            "risk_summary": "test",
            "risk_explanation": "test",
            "confidence_score": 1.5,  # Invalid: > 1.0
        }
        with pytest.raises(ValidationError):
            ClauseResult.model_validate(data)


class TestContractSchemas:
    """Test contract schemas."""

    def test_contract_create_valid(self):
        data = {
            "name": "Test Contract",
            "contract_type": "NDA",
            "party_a": "Company A",
            "party_b": "Company B",
        }
        contract = ContractCreate.model_validate(data)
        assert contract.name == "Test Contract"
        assert contract.contract_type == ContractType.NDA

    def test_contract_create_invalid_type(self):
        data = {
            "name": "Test Contract",
            "contract_type": "INVALID_TYPE",
        }
        with pytest.raises(ValidationError):
            ContractCreate.model_validate(data)


class TestScanJobSchemas:
    """Test scan job schemas."""

    def test_scan_request_valid(self):
        from uuid import uuid4
        data = {
            "contract_id": str(uuid4()),
            "features": {
                "risk_analysis": True,
                "type_detection": False,
            },
        }
        req = ScanRequest.model_validate(data)
        assert req.features.risk_analysis is True
        assert req.features.type_detection is False


class TestValidateLLMResponse:
    """Test the validate_llm_response utility."""

    def test_valid_json_passes(self):
        valid_json = '{"risk_level": "HIGH", "risk_category": "test", "risk_summary": "test", "risk_explanation": "test", "confidence_score": 0.9}'
        result = validate_risk_analysis(valid_json)
        assert result is not None
        assert result.risk_level == RiskLevel.HIGH

    def test_invalid_json_returns_none(self):
        invalid_json = '{"invalid": "data"}'
        result = validate_risk_analysis(invalid_json)
        assert result is None

    def test_dict_input_works(self):
        data = {
            "risk_level": "LOW",
            "risk_category": "test",
            "risk_summary": "test summary",
            "risk_explanation": "test explanation",
            "confidence_score": 0.8,
        }
        result = validate_risk_analysis(data)
        assert result is not None
        assert result.risk_level == RiskLevel.LOW

    def test_missing_field_returns_none(self):
        incomplete = '{"risk_level": "HIGH"}'
        result = validate_risk_analysis(incomplete)
        assert result is None

    def test_invalid_enum_returns_none(self):
        bad_enum = '{"risk_level": "INVALID", "risk_category": "test", "risk_summary": "test", "risk_explanation": "test", "confidence_score": 0.9}'
        result = validate_risk_analysis(bad_enum)
        assert result is None

    def test_markdown_fence_stripping(self):
        with_fence = '```json\n{"risk_level": "MEDIUM", "risk_category": "test", "risk_summary": "test", "risk_explanation": "test", "confidence_score": 0.7}\n```'
        result = validate_risk_analysis(with_fence)
        assert result is not None
        assert result.risk_level == RiskLevel.MEDIUM


class TestLLMResponseModels:
    """Test LLM response Pydantic models."""

    def test_llm_risk_analysis(self):
        data = {
            "risk_level": "CRITICAL",
            "risk_category": "liability",
            "risk_summary": "Unlimited liability exposure",
            "risk_explanation": "This clause provides no liability cap.",
            "recommendations": ["Add cap", "Add exclusion"],
            "confidence_score": 0.95,
        }
        result = LLMRiskAnalysis.model_validate(data)
        assert result.risk_level == RiskLevel.CRITICAL

    def test_llm_type_detection(self):
        data = {
            "contract_type": "NDA",
            "contract_subtype": "Mutual NDA",
            "confidence_score": 0.85,
            "detected_parties": ["Party A", "Party B"],
            "governing_law": "California",
            "reasoning": "Contains standard NDA provisions",
        }
        result = LLMTypeDetection.model_validate(data)
        assert result.contract_type == ContractType.NDA

    def test_llm_consequence(self):
        data = {
            "immediate_consequences": ["Breach risk"],
            "long_term_consequences": ["Legal dispute"],
            "financial_impact": {"estimated_severity": "SEVERE"},
            "operational_impact": {"estimated_severity": "MODERATE"},
            "likelihood": "LIKELY",
            "confidence_score": 0.8,
        }
        result = LLMConsequence.model_validate(data)
        assert result.likelihood == Likelihood.LIKELY


class TestSchemaImports:
    """Test that all schemas can be imported without errors."""

    def test_import_all_enums(self):
        from services.api.app.schemas import (
            RiskLevel, ContractType, ImpactSeverity, Likelihood,
            NegotiationPriority, AcceptanceLikelihood, AsymmetryCategory,
            Enforceability, PrecedentType, ClauseType, ScanStatus,
        )
        assert RiskLevel is not None

    def test_import_all_clause_models(self):
        from services.ai.schemas.llm_responses import (
            LLMRiskAnalysis, LLMTypeDetection, LLMConsequence,
            LLMSummary, LLMPowerAsymmetry, LLMCounterOffer, LLMPrecedent,
        )
        assert LLMRiskAnalysis is not None

    def test_import_validate_functions(self):
        from services.ai.schemas.validate_llm_response import (
            validate_llm_response,
            validate_risk_analysis,
            validate_type_detection,
            validate_consequence,
            validate_summary,
            validate_power_asymmetry,
            validate_counter_offer,
            validate_precedent,
        )
        assert validate_risk_analysis is not None