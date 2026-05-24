"""
Tests for Steps 7.1 (Consequence) and 7.2 (Power Asymmetry).
"""

import pytest
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AI_DIR = os.path.join(PROJECT_ROOT, 'services', 'ai')
if AI_DIR not in sys.path:
    sys.path.insert(0, AI_DIR)
os.chdir(AI_DIR)


class TestConsequencePipeline:
    """Step 7.1: Consequence Generation."""

    def test_risk_level_enum(self):
        from app.pipelines.consequence_generation import RiskLevel
        assert RiskLevel.HIGH.value == "HIGH"
        assert RiskLevel.MEDIUM.value == "MEDIUM"
        assert RiskLevel.LOW.value == "LOW"

    def test_clause_input(self):
        from app.pipelines.consequence_generation import ClauseInput, RiskLevel
        clause = ClauseInput(
            clause_id="1",
            clause_type="indemnity",
            clause_text="shall indemnify",
            risk_level=RiskLevel.HIGH,
            risk_category="Financial",
            user_role="employee",
        )
        assert clause.risk_level == RiskLevel.HIGH

    def test_pipeline_function(self):
        from app.pipelines.consequence_generation import run_consequence_generation
        assert callable(run_consequence_generation)

    def test_low_not_passed(self):
        from app.pipelines.consequence_generation import RiskLevel
        low = RiskLevel.LOW
        assert low != RiskLevel.HIGH


class TestPowerAsymmetryPipeline:
    """Step 7.2: Power Asymmetry."""

    def test_power_result_fields(self):
        from app.pipelines.power_analysis import PowerAsymmetryResult
        result = PowerAsymmetryResult(
            power_score=-100,
            power_label="user_disadvantage",
            key_imbalances=[],
            leverage_points=[],
        )
        assert result.power_score == -100
        assert -100 <= result.power_score <= 100

    def test_balanced(self):
        from app.pipelines.power_analysis import PowerAsymmetryResult
        result = PowerAsymmetryResult(
            power_score=10,
            power_label="balanced",
            key_imbalances=[],
            leverage_points=[],
        )
        assert -20 <= result.power_score <= 20

    def test_user_favorable(self):
        from app.pipelines.power_analysis import PowerAsymmetryResult
        result = PowerAsymmetryResult(
            power_score=75,
            power_label="user_favorable",
            key_imbalances=[],
            leverage_points=[],
        )
        assert result.power_score > 50

    def test_pipeline_function(self):
        from app.pipelines.power_analysis import run_power_asymmetry
        assert callable(run_power_asymmetry)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])