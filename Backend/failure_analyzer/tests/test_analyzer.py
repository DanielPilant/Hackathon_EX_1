"""
Integration Tests for Failure Analyzer

Tests the full analysis pipeline with mock OpenAI.
"""

import pytest
import asyncio
from failure_analyzer.analyzer import FailureAnalyzer, analyze_failure
from failure_analyzer.schemas import FailureCategory
from failure_analyzer.test_fixtures import (
    SAMPLE_FAILURES,
    EXPECTED_CLASSIFICATIONS,
    get_all_failure_fixtures,
    get_non_failure_fixtures
)


@pytest.fixture
def mock_analyzer():
    """Create analyzer with mock OpenAI."""
    return FailureAnalyzer(mock_openai=True)


class TestFailureAnalyzer:
    """Tests for FailureAnalyzer class."""
    
    @pytest.mark.asyncio
    async def test_analyze_timeout_error(self, mock_analyzer):
        """Test full analysis of timeout error."""
        fixture = SAMPLE_FAILURES["timeout_error"]
        
        result = await mock_analyzer.analyze(fixture)
        
        assert "analysis_id" in result
        assert result["failure_category"] == "ELEMENT_NOT_FOUND"
        assert result["failed_step"] == "Click 'Submit'"
        assert "summary" in result
        assert "why" in result
        assert "suggested_fix" in result
        assert 0 <= result["confidence"] <= 1
    
    @pytest.mark.asyncio
    async def test_analyze_assertion_error(self, mock_analyzer):
        """Test full analysis of assertion error."""
        fixture = SAMPLE_FAILURES["assertion_tobe"]
        
        result = await mock_analyzer.analyze(fixture)
        
        assert result["failure_category"] == "ASSERTION_FAILED"
        assert len(result["evidence"]) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_js_error(self, mock_analyzer):
        """Test full analysis of JavaScript error."""
        fixture = SAMPLE_FAILURES["js_typeerror"]
        
        result = await mock_analyzer.analyze(fixture)
        
        assert result["failure_category"] == "JS_ERROR"
    
    @pytest.mark.asyncio
    async def test_analyze_network_error(self, mock_analyzer):
        """Test full analysis of network error."""
        fixture = SAMPLE_FAILURES["network_connection_refused"]
        
        result = await mock_analyzer.analyze(fixture)
        
        assert result["failure_category"] == "NETWORK_FAILURE"
    
    @pytest.mark.asyncio
    async def test_analyze_non_failure_returns_ignored(self, mock_analyzer):
        """Test that non-failure events are ignored."""
        fixture = SAMPLE_FAILURES["non_failure_info"]
        
        result = await mock_analyzer.analyze(fixture)
        
        assert result["status"] == "ignored_non_failure_log"
    
    @pytest.mark.asyncio
    async def test_analyze_missing_fields(self, mock_analyzer):
        """Test analysis with missing fields."""
        fixture = SAMPLE_FAILURES["missing_fields"]
        
        result = await mock_analyzer.analyze(fixture)
        
        # Should still produce valid analysis
        assert "analysis_id" in result
        assert "failure_category" in result
    
    @pytest.mark.asyncio
    async def test_analyze_empty_event(self, mock_analyzer):
        """Test analysis of empty event."""
        result = await mock_analyzer.analyze({})
        
        # Empty events should be ignored
        assert result.get("status") == "ignored_non_failure_log" or "analysis_id" in result
    
    @pytest.mark.asyncio
    async def test_confidence_is_bounded(self, mock_analyzer):
        """Test that confidence is always between 0 and 1."""
        for name, fixture in get_all_failure_fixtures().items():
            result = await mock_analyzer.analyze(fixture)
            
            if "confidence" in result:
                assert 0 <= result["confidence"] <= 1, \
                    f"Confidence out of bounds for {name}: {result['confidence']}"


class TestAnalyzerSyncWrapper:
    """Tests for synchronous wrapper."""
    
    def test_analyze_sync(self):
        """Test synchronous analysis."""
        analyzer = FailureAnalyzer(mock_openai=True)
        fixture = SAMPLE_FAILURES["timeout_error"]
        
        result = analyzer.analyze_sync(fixture)
        
        assert "analysis_id" in result
        assert result["failure_category"] == "ELEMENT_NOT_FOUND"


class TestAnalyzeBatch:
    """Tests for batch analysis."""
    
    @pytest.mark.asyncio
    async def test_analyze_batch(self, mock_analyzer):
        """Test batch analysis of multiple events."""
        fixtures = [
            SAMPLE_FAILURES["timeout_error"],
            SAMPLE_FAILURES["assertion_tobe"],
            SAMPLE_FAILURES["non_failure_info"]
        ]
        
        results = await mock_analyzer.analyze_batch(fixtures)
        
        assert len(results) == 3
        assert results[0]["failure_category"] == "ELEMENT_NOT_FOUND"
        assert results[1]["failure_category"] == "ASSERTION_FAILED"
        assert results[2]["status"] == "ignored_non_failure_log"


class TestAnalyzeFailureFunction:
    """Tests for convenience function."""
    
    @pytest.mark.asyncio
    async def test_analyze_failure_function(self):
        """Test the analyze_failure convenience function."""
        fixture = SAMPLE_FAILURES["timeout_error"]
        
        result = await analyze_failure(fixture, mock=True)
        
        assert "analysis_id" in result
        assert result["failure_category"] == "ELEMENT_NOT_FOUND"


class TestAllFixtures:
    """Test all fixtures produce valid output."""
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("fixture_name", list(get_all_failure_fixtures().keys()))
    async def test_all_failure_fixtures_analyzed(self, mock_analyzer, fixture_name):
        """Test that all failure fixtures produce valid analysis."""
        fixture = SAMPLE_FAILURES[fixture_name]
        
        result = await mock_analyzer.analyze(fixture)
        
        # Should have all required fields
        assert "analysis_id" in result
        assert "failure_category" in result
        assert "summary" in result
        assert "why" in result
        assert "suggested_fix" in result
        assert "evidence" in result
        assert "confidence" in result
        
        # Evidence should be a list
        assert isinstance(result["evidence"], list)
        
        # Summary should not be empty
        assert len(result["summary"]) > 0
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("fixture_name", list(get_non_failure_fixtures().keys()))
    async def test_all_non_failure_fixtures_ignored(self, mock_analyzer, fixture_name):
        """Test that non-failure fixtures are ignored."""
        fixture = SAMPLE_FAILURES[fixture_name]
        
        result = await mock_analyzer.analyze(fixture)
        
        assert result["status"] == "ignored_non_failure_log"


class TestErrorHandling:
    """Tests for error handling."""
    
    @pytest.mark.asyncio
    async def test_handles_none_input(self, mock_analyzer):
        """Test handling of None input."""
        # This should not raise an exception
        result = await mock_analyzer.analyze(None)
        
        # Should return ignored or error analysis
        assert "status" in result or "analysis_id" in result
    
    @pytest.mark.asyncio
    async def test_handles_invalid_input_type(self, mock_analyzer):
        """Test handling of invalid input types."""
        result = await mock_analyzer.analyze("not a dict")
        
        assert "status" in result or "analysis_id" in result
    
    @pytest.mark.asyncio
    async def test_handles_deeply_nested_event(self, mock_analyzer):
        """Test handling of deeply nested events."""
        event = {
            "a": {"b": {"c": {"d": {"e": {"message": "TimeoutError"}}}}}
        }
        
        # Should not raise an exception
        result = await mock_analyzer.analyze(event)
        assert result is not None
