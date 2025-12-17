"""
Unit Tests for Normalizer

Tests field extraction from various MCP JSON formats.
"""

import pytest
from failure_analyzer.normalizer import (
    normalize_mcp_event,
    is_failure_event,
    _extract_locator_hints,
    _deep_get
)
from failure_analyzer.test_fixtures import SAMPLE_FAILURES


class TestNormalizeMcpEvent:
    """Tests for normalize_mcp_event function."""
    
    def test_standard_mcp_format(self):
        """Test extraction from standard MCP format."""
        event = {
            "type": "log",
            "payload": {
                "message": "TimeoutError: Timeout 30000ms exceeded",
                "stepName": "Click Submit",
                "console": ["console log 1"],
                "network": [{"url": "http://example.com", "status": 200}]
            }
        }
        
        result = normalize_mcp_event(event)
        
        assert result is not None
        assert "TimeoutError" in result.raw_message
        assert result.step == "Click Submit"
        assert len(result.console_lines) == 1
        assert len(result.network_lines) == 1
    
    def test_alternative_field_names(self):
        """Test extraction with alternative field names."""
        event = {
            "type": "error",
            "errorMessage": "AssertionError: expected true",
            "action": "Verify checkbox",
            "consoleLogs": ["log entry"],
            "networkLogs": []
        }
        
        result = normalize_mcp_event(event)
        
        assert result is not None
        assert "AssertionError" in result.raw_message
        assert result.step == "Verify checkbox"
    
    def test_nested_structure(self):
        """Test extraction from nested structures."""
        event = SAMPLE_FAILURES["nested_structure"]
        
        result = normalize_mcp_event(event)
        
        assert result is not None
        assert "Timeout" in result.raw_message or "timeout" in result.raw_message.lower()
    
    def test_missing_fields(self):
        """Test handling of missing fields."""
        event = {
            "type": "error",
            "data": "Some error occurred"
        }
        
        result = normalize_mcp_event(event)
        
        assert result is not None
        assert result.step is None
        assert result.console_lines == []
        assert result.network_lines == []
    
    def test_empty_event(self):
        """Test handling of empty event."""
        result = normalize_mcp_event({})
        
        # Empty dict with no error indicators returns None
        # This is expected behavior - empty events aren't failures
        # If we want to handle empty events, we need at least some content
        assert result is None or result.raw_message == ""
    
    def test_none_input(self):
        """Test handling of None input."""
        result = normalize_mcp_event(None)
        assert result is None
    
    def test_invalid_input_type(self):
        """Test handling of invalid input type."""
        result = normalize_mcp_event("not a dict")
        assert result is None
    
    def test_locator_extraction(self):
        """Test extraction of locator hints from error message."""
        event = {
            "type": "error",
            "payload": {
                "message": 'TimeoutError waiting for locator("text=Submit Button")'
            }
        }
        
        result = normalize_mcp_event(event)
        
        assert result is not None
        assert "text=Submit Button" in result.locator_hints
    
    def test_raw_event_preserved(self):
        """Test that raw event is preserved in result."""
        event = {"type": "error", "custom_field": "custom_value"}
        
        result = normalize_mcp_event(event)
        
        assert result is not None
        assert result.raw_event == event


class TestIsFailureEvent:
    """Tests for is_failure_event function."""
    
    def test_error_type(self):
        """Test detection of error type events."""
        assert is_failure_event({"type": "error"}) is True
        assert is_failure_event({"type": "fail"}) is True
        assert is_failure_event({"type": "failure"}) is True
    
    def test_error_level(self):
        """Test detection by log level."""
        assert is_failure_event({"level": "error"}) is True
        assert is_failure_event({"level": "fatal"}) is True
        assert is_failure_event({"level": "critical"}) is True
    
    def test_error_in_message(self):
        """Test detection by error keywords in message."""
        assert is_failure_event({"message": "TimeoutError occurred"}) is True
        assert is_failure_event({"payload": {"message": "Test failed"}}) is True
    
    def test_status_field(self):
        """Test detection by status field."""
        assert is_failure_event({"status": "fail"}) is True
        assert is_failure_event({"status": "failed"}) is True
        assert is_failure_event({"status": "error"}) is True
    
    def test_non_failure_events(self):
        """Test that non-failure events return False."""
        assert is_failure_event({"type": "log", "level": "info"}) is False
        assert is_failure_event({"type": "log", "message": "Step completed"}) is False
        assert is_failure_event({"status": "pass"}) is False
    
    def test_sample_fixtures(self):
        """Test is_failure_event with sample fixtures."""
        # Failure fixtures should be detected
        for name, fixture in SAMPLE_FAILURES.items():
            if name.startswith("non_failure"):
                assert is_failure_event(fixture) is False, f"{name} should not be a failure"
            else:
                assert is_failure_event(fixture) is True, f"{name} should be a failure"


class TestExtractLocatorHints:
    """Tests for _extract_locator_hints function."""
    
    def test_locator_function_pattern(self):
        """Test extraction from locator() function calls."""
        text = 'Error: waiting for locator("text=Submit")'
        hints = _extract_locator_hints(text)
        assert "text=Submit" in hints
    
    def test_text_selector(self):
        """Test extraction of text= selectors."""
        text = "Timeout waiting for text=Login Button"
        hints = _extract_locator_hints(text)
        assert "Login" in hints or "text=Login" in " ".join(hints)
    
    def test_id_selector(self):
        """Test extraction of #id selectors."""
        text = "Element #submitBtn not found"
        hints = _extract_locator_hints(text)
        assert "submitBtn" in hints
    
    def test_class_selector(self):
        """Test extraction of .class selectors."""
        text = "Could not find .btn-primary"
        hints = _extract_locator_hints(text)
        assert "btn-primary" in hints
    
    def test_data_testid(self):
        """Test extraction of data-testid selectors."""
        text = 'Element [data-testid="login-form"] not visible'
        hints = _extract_locator_hints(text)
        assert "login-form" in hints
    
    def test_multiple_hints(self):
        """Test extraction of multiple hints."""
        text = 'locator("text=Submit") in #formContainer .button-row'
        hints = _extract_locator_hints(text)
        assert len(hints) >= 2


class TestDeepGet:
    """Tests for _deep_get helper function."""
    
    def test_simple_key(self):
        """Test getting a simple key."""
        data = {"message": "hello"}
        assert _deep_get(data, ["message"]) == "hello"
    
    def test_multiple_key_options(self):
        """Test trying multiple keys."""
        data = {"msg": "hello"}
        assert _deep_get(data, ["message", "msg", "text"]) == "hello"
    
    def test_nested_key(self):
        """Test getting from nested structure."""
        data = {"payload": {"message": "nested hello"}}
        assert _deep_get(data, ["message"]) == "nested hello"
    
    def test_default_value(self):
        """Test default value when key not found."""
        data = {"other": "value"}
        assert _deep_get(data, ["message"], "default") == "default"
    
    def test_non_dict_input(self):
        """Test handling of non-dict input."""
        assert _deep_get("string", ["key"], "default") == "default"
        assert _deep_get(None, ["key"], "default") == "default"
