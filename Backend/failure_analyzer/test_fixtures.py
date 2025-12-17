"""
Test Fixtures for Failure Analyzer

Sample MCP events covering all failure categories for isolated testing.
"""

from typing import Dict, Any

# Sample failure events covering all categories
SAMPLE_FAILURES: Dict[str, Dict[str, Any]] = {
    # ELEMENT_NOT_FOUND - Timeout waiting for element
    "timeout_error": {
        "type": "log",
        "payload": {
            "message": "TimeoutError: Timeout 30000ms exceeded waiting for locator(\"text=Submit\")",
            "stepName": "Click 'Submit'",
            "console": [],
            "network": []
        }
    },
    
    # ELEMENT_NOT_FOUND - Element not found variant
    "element_not_found": {
        "type": "error",
        "payload": {
            "message": "Error: locator resolved to 0 elements. Expected at least 1 element matching selector '.btn-primary'",
            "step": "Click primary button",
            "console": ["Warning: Button not rendered"],
            "network": []
        }
    },
    
    # ASSERTION_FAILED - expect().toBe() failure
    "assertion_tobe": {
        "type": "log",
        "payload": {
            "message": "AssertionError: expect(received).toBe(expected)\n\nExpected: 'Welcome, User!'\nReceived: 'Login Failed'",
            "stepName": "Verify login success message",
            "console": [],
            "network": []
        }
    },
    
    # ASSERTION_FAILED - toContain failure
    "assertion_contain": {
        "type": "log",
        "payload": {
            "message": "Error: expect(received).toContain(expected)\n\nExpected: 'Dashboard'\nReceived: 'Error Page'",
            "stepName": "Verify navigation to dashboard",
            "console": [],
            "network": []
        }
    },
    
    # JS_ERROR - TypeError
    "js_typeerror": {
        "type": "log",
        "payload": {
            "message": "TypeError: Cannot read properties of undefined (reading 'click')",
            "stepName": "Interact with modal",
            "console": [
                "Uncaught TypeError at app.js:145",
                "    at handleClick (app.js:145:23)",
                "    at HTMLButtonElement.onclick (index.html:52:1)"
            ],
            "network": []
        }
    },
    
    # JS_ERROR - ReferenceError
    "js_referenceerror": {
        "type": "error",
        "payload": {
            "message": "ReferenceError: userData is not defined",
            "step": "Load user profile",
            "console": ["ReferenceError: userData is not defined at profile.js:23"],
            "network": []
        }
    },
    
    # NETWORK_FAILURE - Connection refused
    "network_connection_refused": {
        "type": "log",
        "payload": {
            "message": "net::ERR_CONNECTION_REFUSED at https://api.example.com/login",
            "stepName": "Submit login form",
            "console": ["Failed to load resource: net::ERR_CONNECTION_REFUSED"],
            "network": [
                {"url": "https://api.example.com/login", "status": 0, "error": "CONNECTION_REFUSED"}
            ]
        }
    },
    
    # NETWORK_FAILURE - HTTP 500 error
    "network_http_500": {
        "type": "error",
        "payload": {
            "message": "Request failed with status code 500",
            "step": "Fetch user data",
            "console": [],
            "network": [
                {"url": "https://api.example.com/users/123", "status": 500, "statusText": "Internal Server Error"}
            ]
        }
    },
    
    # NETWORK_FAILURE - HTTP 404 error
    "network_http_404": {
        "type": "log",
        "payload": {
            "message": "HTTP 404: Resource not found",
            "stepName": "Load product details",
            "console": ["GET /api/products/999 - 404 Not Found"],
            "network": [
                {"url": "/api/products/999", "status": 404}
            ]
        }
    },
    
    # UNKNOWN - Generic error
    "unknown_error": {
        "type": "log",
        "payload": {
            "message": "Something unexpected happened during test execution",
            "stepName": "Unknown step",
            "console": [],
            "network": []
        }
    },
    
    # Edge case: Missing fields
    "missing_fields": {
        "type": "error",
        "data": "TimeoutError: element not found"
    },
    
    # Edge case: Nested structure
    "nested_structure": {
        "event": {
            "error": {
                "msg": "Timeout 5000ms exceeded waiting for locator"
            },
            "context": {
                "step": "Click submit button"
            }
        }
    },
    
    # Edge case: Alternative field names
    "alt_field_names": {
        "type": "failure",
        "errorMessage": "AssertionError: expected 'true' to equal 'false'",
        "action": "Verify checkbox state",
        "consoleLogs": ["Checkbox was not checked as expected"],
        "networkLogs": []
    },
    
    # Non-failure event (should be ignored)
    "non_failure_info": {
        "type": "log",
        "payload": {
            "level": "info",
            "message": "Test step completed successfully",
            "stepName": "Navigate to home"
        }
    },
    
    # Non-failure event - success
    "non_failure_success": {
        "type": "result",
        "status": "pass",
        "message": "All assertions passed"
    }
}


# Expected classifications for each fixture
EXPECTED_CLASSIFICATIONS = {
    "timeout_error": "ELEMENT_NOT_FOUND",
    "element_not_found": "ELEMENT_NOT_FOUND",
    "assertion_tobe": "ASSERTION_FAILED",
    "assertion_contain": "ASSERTION_FAILED",
    "js_typeerror": "JS_ERROR",
    "js_referenceerror": "JS_ERROR",
    "network_connection_refused": "NETWORK_FAILURE",
    "network_http_500": "NETWORK_FAILURE",
    "network_http_404": "NETWORK_FAILURE",
    "unknown_error": "UNKNOWN",
    "missing_fields": "ELEMENT_NOT_FOUND",  # Contains "TimeoutError"
    "nested_structure": "ELEMENT_NOT_FOUND",  # Contains "Timeout"
    "alt_field_names": "ASSERTION_FAILED",
}


def get_fixture(name: str) -> Dict[str, Any]:
    """Get a specific test fixture by name."""
    if name not in SAMPLE_FAILURES:
        raise KeyError(f"Unknown fixture: {name}. Available: {list(SAMPLE_FAILURES.keys())}")
    return SAMPLE_FAILURES[name]


def get_all_failure_fixtures() -> Dict[str, Dict[str, Any]]:
    """Get all fixtures that represent failures (excluding non-failures)."""
    return {
        name: fixture
        for name, fixture in SAMPLE_FAILURES.items()
        if not name.startswith("non_failure")
    }


def get_non_failure_fixtures() -> Dict[str, Dict[str, Any]]:
    """Get fixtures that should NOT be classified as failures."""
    return {
        name: fixture
        for name, fixture in SAMPLE_FAILURES.items()
        if name.startswith("non_failure")
    }
