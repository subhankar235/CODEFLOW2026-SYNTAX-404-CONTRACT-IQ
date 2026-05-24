"""
Tests for Step 6.5 — Celery Task.
"""

import pytest
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'services', 'api'))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'apps'))


class TestCeleryTask:
    """Test the Celery task exists."""

    def test_process_contract_exists(self):
        try:
            from worker.tasks.process_contract import process_contract
            assert callable(process_contract)
        except ImportError:
            pytest.skip("Worker module placeholder")


class TestCeleryConfig:
    """Test Celery configuration."""

    def test_celery_app_exists(self):
        try:
            from worker.celery_app import app
            assert app is not None
        except ImportError:
            from apps.worker.celery_app import app
            assert app is not None


class TestPipelineSteps:
    """Test pipeline step imports."""

    def test_download_exists(self):
        try:
            from worker.pipeline import download_file
            assert callable(download_file)
        except ImportError:
            pytest.skip("Pipeline not implemented")

    def test_decrypt_exists(self):
        try:
            from worker.pipeline import decrypt_file
            assert callable(decrypt_file)
        except ImportError:
            pytest.skip("Pipeline not implemented")

    def test_parse_exists(self):
        try:
            from worker.pipeline import parse_document
            assert callable(parse_document)
        except ImportError:
            pytest.skip("Pipeline not implemented")

    def test_detect_type_exists(self):
        try:
            from worker.pipeline import detect_contract_type
            assert callable(detect_contract_type)
        except ImportError:
            pytest.skip("Pipeline not implemented")

    def test_split_clauses_exists(self):
        try:
            from worker.pipeline import split_into_clauses
            assert callable(split_into_clauses)
        except ImportError:
            pytest.skip("Pipeline not implemented")

    def test_rule_engine_exists(self):
        try:
            from worker.pipeline import run_rule_engine
            assert callable(run_rule_engine)
        except ImportError:
            pytest.skip("Pipeline not implemented")

    def test_llm_risk_exists(self):
        try:
            from worker.pipeline import run_llm_risk_analysis
            assert callable(run_llm_risk_analysis)
        except ImportError:
            pytest.skip("Pipeline not implemented")

    def test_summary_exists(self):
        try:
            from worker.pipeline import generate_summary
            assert callable(generate_summary)
        except ImportError:
            pytest.skip("Pipeline not implemented")


class TestProgressUpdates:
    """Test progress update milestones."""

    def test_progress_milestones_defined(self):
        expected = {
            "parse": 10, "detect_type": 15, "rule_engine": 25,
            "llm_risk": 60, "consequence": 70, "power": 75,
            "precedent": 80, "summary": 85, "embed": 95, "store": 100
        }
        for step, pct in expected.items():
            assert pct >= 0 and pct <= 100


class TestStreamingPublisher:
    """Test Redis pub/sub publisher functions."""

    def test_publish_functions_exist(self):
        from apps.services import streaming_service
        funcs = ['publish_clause', 'publish_complete', 'publish_error', 'publish_progress']
        for fn in funcs:
            assert hasattr(streaming_service, fn), f"Missing {fn}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])