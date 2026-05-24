"""
Tests for Step 7.3 (Summary Card Pipeline).
"""

import pytest
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AI_DIR = os.path.join(PROJECT_ROOT, 'services', 'ai')
if AI_DIR not in sys.path:
    sys.path.insert(0, AI_DIR)
os.chdir(AI_DIR)


class TestSummaryCardPipeline:
    """Step 7.3: Summary Card Generation."""

    def test_summary_card_model(self):
        from app.pipelines.summary import SummaryCard
        card = SummaryCard(
            one_liner="This contract favors the employer.",
            should_you_sign="Yes with changes",
            top_3_concerns=["concern1", "concern2", "concern3"],
            top_2_positives=["positive1", "positive2"],
            overall_risk_score=65,
            negotiating_power="Weak",
        )
        assert card.should_you_sign in ["Yes as-is", "Yes with changes", "No"]

    def test_should_you_sign_validation(self):
        from app.pipelines.summary import SummaryCard
        # Valid values
        for v in ["Yes as-is", "Yes with changes", "No"]:
            card = SummaryCard(
                one_liner="test",
                should_you_sign=v,
                top_3_concerns=["1", "2", "3"],
                top_2_positives=["a", "b"],
                overall_risk_score=50,
                negotiating_power="Moderate",
            )
            assert card.should_you_sign == v

    def test_risk_score_range(self):
        from app.pipelines.summary import SummaryCard
        # Boundary tests
        card = SummaryCard(
            one_liner="test",
            should_you_sign="Yes as-is",
            top_3_concerns=["1", "2", "3"],
            top_2_positives=["a", "b"],
            overall_risk_score=0,
            negotiating_power="Strong",
        )
        assert card.overall_risk_score == 0

        card = SummaryCard(
            one_liner="test",
            should_you_sign="No",
            top_3_concerns=["1", "2", "3"],
            top_2_positives=["a", "b"],
            overall_risk_score=100,
            negotiating_power="Weak",
        )
        assert card.overall_risk_score == 100

    def test_negotiating_power_values(self):
        from app.pipelines.summary import SummaryCard
        for v in ["Strong", "Moderate", "Weak"]:
            card = SummaryCard(
                one_liner="test",
                should_you_sign="Yes with changes",
                top_3_concerns=["1", "2", "3"],
                top_2_positives=["a", "b"],
                overall_risk_score=50,
                negotiating_power=v,
            )
            assert card.negotiating_power == v

    def test_top_3_concerns_exactly_3(self):
        from app.pipelines.summary import SummaryCard
        card = SummaryCard(
            one_liner="test",
            should_you_sign="Yes with changes",
            top_3_concerns=["a", "b", "c"],
            top_2_positives=["x", "y"],
            overall_risk_score=50,
            negotiating_power="Moderate",
        )
        assert len(card.top_3_concerns) == 3

    def test_top_2_positives_exactly_2(self):
        from app.pipelines.summary import SummaryCard
        card = SummaryCard(
            one_liner="test",
            should_you_sign="Yes with changes",
            top_3_concerns=["a", "b", "c"],
            top_2_positives=["x", "y"],
            overall_risk_score=50,
            negotiating_power="Moderate",
        )
        assert len(card.top_2_positives) == 2

    def test_pros_cons_snapshot(self):
        from app.pipelines.summary import ProsConsSnapshot
        snapshot = ProsConsSnapshot(
            pros=[{"dimension": "Financial", "text": "Good pay"}],
            cons=[{"dimension": "Liability", "text": "Unlimited liability"}],
            verdict="Negotiate changes",
        )
        assert len(snapshot.pros) == 1
        assert len(snapshot.cons) == 1

    def test_pipeline_function(self):
        from app.pipelines.summary import run_summary
        assert callable(run_summary)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])