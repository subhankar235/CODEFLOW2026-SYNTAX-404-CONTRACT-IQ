"""
Tests for Step 6.2 — Regex Rules (Risk Pattern Detection).
"""

import pytest

from services.ai.app.rules.regex_rules import (
    RiskCategory,
    RiskLevel,
    RiskPattern,
    ALL_PATTERNS,
    get_all_patterns,
    get_patterns_by_category,
    get_high_risk_patterns,
)


class TestRiskCategoryEnum:
    """Test RiskCategory enum values match PRD.md."""

    def test_indemnity_present(self):
        assert RiskCategory.INDEMNITY.value == "indemnity"

    def test_ip_assignment_present(self):
        assert RiskCategory.IP_ASSIGNMENT.value == "ip_assignment"

    def test_non_compete_present(self):
        assert RiskCategory.NON_COMPETE.value == "non_compete"

    def test_auto_renewal_present(self):
        assert RiskCategory.AUTO_RENEWAL.value == "auto_renewal"

    def test_all_categories_from_prd_present(self):
        expected_categories = {
            "indemnity",
            "ip_assignment",
            "non_compete",
            "auto_renewal",
            "limitation_of_liability",
            "termination_for_convenience",
            "unilateral_modification",
            "liquidated_damages",
            "arbitration_only",
            "payment_clawback",
        }
        actual_categories = {c.value for c in RiskCategory}
        assert expected_categories.issubset(actual_categories)


class TestRiskLevelEnum:
    """Test RiskLevel enum."""

    def test_high_level(self):
        assert RiskLevel.HIGH.value == "HIGH"

    def test_medium_level(self):
        assert RiskLevel.MEDIUM.value == "MEDIUM"


class TestPatternCount:
    """Test that there are 40+ patterns."""

    def test_at_least_40_patterns(self):
        assert len(ALL_PATTERNS) >= 40


class TestIndemnityPatterns:
    """Test indemnity risk detection."""

    def test_indemnify_hold_harmless_detected(self):
        pattern = next(p for p in ALL_PATTERNS if p.name == "indemnify_hold_harmless")
        text = "The party shall indemnify and hold harmless the other party from any claims."
        assert pattern.matches(text) is True
        assert pattern.risk_level == RiskLevel.HIGH

    def test_broad_indemnity_detected(self):
        pattern = next(p for p in ALL_PATTERNS if p.name == "indemnify_defend")
        text = "Company agrees to indemnify and defend Client against all damages."
        assert pattern.matches(text) is True


class TestIPAssignmentPatterns:
    """Test IP assignment risk detection."""

    def test_all_ip_created_detected(self):
        pattern = next(p for p in ALL_PATTERNS if p.name == "all_ip_created")
        text = "Employee agrees that all intellectual property created during employment belongs to Employer."
        assert pattern.matches(text) is True
        assert pattern.risk_level == RiskLevel.HIGH

    def test_work_for_hire_detected(self):
        pattern = next(p for p in ALL_PATTERNS if p.name == "work_for_hire")
        text = "Work made for hire"
        assert pattern.matches(text) is True


class TestNonCompetePatterns:
    """Test non-compete risk detection."""

    def test_non_compete_explicit_detected(self):
        pattern = next(p for p in ALL_PATTERNS if p.name == "non_compete_explicit")
        text = "Employee agrees to a non-compete covenant for 2 years."
        assert pattern.matches(text) is True
        assert pattern.risk_level == RiskLevel.HIGH

    def test_restrict_competing_business_detected(self):
        pattern = next(p for p in ALL_PATTERNS if p.name == "restrict_competing_business")
        text = "Employee shall not engage in any competing business."
        assert pattern.matches(text) is True


class TestAutoRenewalPatterns:
    """Test auto-renewal risk detection."""

    def test_automatically_renew_detected(self):
        pattern = next(p for p in ALL_PATTERNS if p.name == "automatically_renew")
        text = "The agreement shall automatically renew for successive one-year terms."
        assert pattern.matches(text) is True
        assert pattern.risk_level == RiskLevel.MEDIUM

    def test_evergreen_clause_detected(self):
        pattern = next(p for p in ALL_PATTERNS if p.name == "evergreen_clause")
        text = "This agreement shall continue unless written notice is given."
        assert pattern.matches(text) is True


class TestLimitationOfLiabilityPatterns:
    """Test limitation of liability detection."""

    def test_no_consequential_damages_detected(self):
        pattern = next(p for p in ALL_PATTERNS if p.name == "no_consequential_damages")
        text = "In no event shall either party be liable for consequential damages."
        assert pattern.matches(text) is True

    def test_liability_cap_detected(self):
        pattern = next(p for p in ALL_PATTERNS if p.name == "liability_cap")
        text = "Total liability shall not exceed the fees paid in the preceding 12 months."
        assert pattern.matches(text) is True


class TestTerminationPatterns:
    """Test termination for convenience detection."""

    def test_terminate_for_convenience_detected(self):
        pattern = next(p for p in ALL_PATTERNS if p.name == "terminate_for_convenience")
        text = "Company may terminate this agreement for convenience at any time."
        assert pattern.matches(text) is True
        assert pattern.risk_level == RiskLevel.HIGH

    def test_terminate_immediately_detected(self):
        pattern = next(p for p in ALL_PATTERNS if p.name == "terminate_immediately")
        text = "Either party may terminate immediately without notice."
        assert pattern.matches(text) is True


class TestUnilateralModificationPatterns:
    """Test unilateral modification detection."""

    def test_unilateral_modification_detected(self):
        pattern = next(p for p in ALL_PATTERNS if p.name == "unilateral_modification")
        text = "Company may modify these terms at any time without notice."
        assert pattern.matches(text) is True
        assert pattern.risk_level == RiskLevel.HIGH

    def test_deemed_acceptance_detected(self):
        pattern = next(p for p in ALL_PATTERNS if p.name == "deemed_acceptance_modification")
        text = "Continued use of the service constitutes acceptance of changes."
        assert pattern.matches(text) is True


class TestLiquidatedDamagesPatterns:
    """Test liquidated damages detection."""

    def test_liquidated_damages_detected(self):
        pattern = next(p for p in ALL_PATTERNS if p.name == "liquidated_damages")
        text = "Liquidated damages of $5,000 shall be paid upon breach."
        assert pattern.matches(text) is True
        assert pattern.risk_level == RiskLevel.HIGH

    def test_penalty_provision_detected(self):
        pattern = next(p for p in ALL_PATTERNS if p.name == "penalty_provision")
        text = "Party agrees to pay $10,000 as a penalty."
        assert pattern.matches(text) is True


class TestArbitrationPatterns:
    """Test arbitration-only detection."""

    def test_mandatory_arbitration_detected(self):
        pattern = next(p for p in ALL_PATTERNS if p.name == "mandatory_arbitration")
        text = "All disputes shall be resolved through mandatory binding arbitration."
        assert pattern.matches(text) is True
        assert pattern.risk_level == RiskLevel.HIGH

    def test_waive_class_action_detected(self):
        pattern = next(p for p in ALL_PATTERNS if p.name == "waive_class_action")
        text = "Employee waives the right to bring class actions."
        assert pattern.matches(text) is True


class TestClawbackPatterns:
    """Test payment clawback detection."""

    def test_clawback_detected(self):
        pattern = next(p for p in ALL_PATTERNS if p.name == "clawback_provision")
        text = "Company may clawback bonuses if employee leaves within 1 year."
        assert pattern.matches(text) is True

    def test_recoupment_detected(self):
        pattern = next(p for p in ALL_PATTERNS if p.name == "recoupment")
        text = "Company may recoup bonuses upon termination."
        assert pattern.matches(text) is True


class TestPatternAccessors:
    """Test pattern accessor functions."""

    def test_get_all_patterns(self):
        patterns = get_all_patterns()
        assert len(patterns) >= 40

    def test_get_patterns_by_category(self):
        indemnity_patterns = get_patterns_by_category(RiskCategory.INDEMNITY)
        assert len(indemnity_patterns) > 0
        assert all(p.category == RiskCategory.INDEMNITY for p in indemnity_patterns)

    def test_get_high_risk_patterns(self):
        high_patterns = get_high_risk_patterns()
        assert len(high_patterns) > 0
        assert all(p.risk_level == RiskLevel.HIGH for p in high_patterns)


class TestRiskPatternMethods:
    """Test RiskPattern methods."""

    def test_matches_returns_bool(self):
        pattern = ALL_PATTERNS[0]
        assert isinstance(pattern.matches("some text"), bool)

    def test_find_matches_returns_list(self):
        pattern = next(p for p in ALL_PATTERNS if p.name == "indemnify_hold_harmless")
        text = "shall indemnify and hold harmless"
        matches = pattern.find_matches(text)
        assert isinstance(matches, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])