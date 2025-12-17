"""
Pytest configuration and shared fixtures.
"""

import pytest
import sys
from pathlib import Path

# Ensure the Backend directory is in the path
backend_dir = Path(__file__).parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))


@pytest.fixture
def mock_analyzer():
    """Create analyzer with mock OpenAI for testing."""
    from failure_analyzer import FailureAnalyzer
    return FailureAnalyzer(mock_openai=True)


@pytest.fixture
def sample_timeout_event():
    """Sample timeout error event."""
    return {
        "type": "log",
        "payload": {
            "message": "TimeoutError: Timeout 30000ms exceeded waiting for locator(\"text=Submit\")",
            "stepName": "Click 'Submit'",
            "console": [],
            "network": []
        }
    }


@pytest.fixture
def sample_assertion_event():
    """Sample assertion error event."""
    return {
        "type": "log",
        "payload": {
            "message": "AssertionError: expect(received).toBe(expected)\nExpected: 'Welcome'\nReceived: 'Login Failed'",
            "stepName": "Verify login success",
            "console": [],
            "network": []
        }
    }


@pytest.fixture
def sample_js_error_event():
    """Sample JavaScript error event."""
    return {
        "type": "log",
        "payload": {
            "message": "TypeError: Cannot read properties of undefined (reading 'click')",
            "stepName": "Interact with modal",
            "console": ["Uncaught TypeError at app.js:145"],
            "network": []
        }
    }


@pytest.fixture
def sample_network_error_event():
    """Sample network error event."""
    return {
        "type": "log",
        "payload": {
            "message": "net::ERR_CONNECTION_REFUSED at https://api.example.com/login",
            "stepName": "Submit login form",
            "console": [],
            "network": [{"url": "https://api.example.com/login", "status": 0}]
        }
    }


@pytest.fixture
def sample_non_failure_event():
    """Sample non-failure event that should be ignored."""
    return {
        "type": "log",
        "payload": {
            "level": "info",
            "message": "Test step completed successfully",
            "stepName": "Navigate to home"
        }
    }
