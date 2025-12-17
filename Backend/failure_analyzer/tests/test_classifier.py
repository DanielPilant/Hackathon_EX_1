"""
Unit Tests for Classifier

Tests rule-based failure classification.
"""

import pytest
from failure_analyzer.classifier import (
    classify_failure,
    get_category_description,
    CLASSIFICATION_RULES
)
from failure_analyzer.schemas import NormalizedFailure, FailureCategory
from failure_analyzer.normalizer import normalize_mcp_event
from failure_analyzer.test_fixtures import (
    SAMPLE_FAILURES,
    EXPECTED_CLASSIFICATIONS,
    get_all_failure_fixtures
)


class TestClassifyFailure:
    """Tests for classify_failure function."""
    
    def test_timeout_error_classification(self):
        """Test classification of timeout errors."""
        normalized = NormalizedFailure(
            raw_message="TimeoutError: Timeout 30000ms exceeded waiting for locator",
            step="Click Submit"
        )
        
        result = classify_failure(normalized)
        
        assert result.category == FailureCategory.ELEMENT_NOT_FOUND
        assert len(result.evidence) > 0
        assert any("Timeout" in ev for ev in result.evidence)
    
    def test_assertion_error_classification(self):
        """Test classification of assertion failures."""
        normalized = NormalizedFailure(
            raw_message="AssertionError: expect(received).toBe(expected)\nExpected: 'true'\nReceived: 'false'",
            step="Verify checkbox"
        )
        
        result = classify_failure(normalized)
        
        assert result.category == FailureCategory.ASSERTION_FAILED
        assert len(result.evidence) > 0
    
    def test_js_error_classification(self):
        """Test classification of JavaScript errors."""
        normalized = NormalizedFailure(
            raw_message="TypeError: Cannot read properties of undefined (reading 'click')",
            step="Click modal",
            console_lines=["Uncaught TypeError at script.js:42"]
        )
        
        result = classify_failure(normalized)
        
        assert result.category == FailureCategory.JS_ERROR
        assert len(result.evidence) > 0
    
    def test_network_error_classification(self):
        """Test classification of network errors."""
        normalized = NormalizedFailure(
            raw_message="net::ERR_CONNECTION_REFUSED",
            step="Submit form",
            network_lines=[{"url": "http://api.example.com", "status": 0}]
        )
        
        result = classify_failure(normalized)
        
        assert result.category == FailureCategory.NETWORK_FAILURE
        assert len(result.evidence) > 0
    
    def test_http_500_classification(self):
        """Test classification of HTTP 500 errors."""
        normalized = NormalizedFailure(
            raw_message="Request failed with status code 500",
            network_lines=[{"url": "/api/users", "status": 500}]
        )
        
        result = classify_failure(normalized)
        
        assert result.category == FailureCategory.NETWORK_FAILURE
    
    def test_unknown_error_classification(self):
        """Test classification falls back to UNKNOWN."""
        normalized = NormalizedFailure(
            raw_message="Something went wrong",
            step="Unknown action"
        )
        
        result = classify_failure(normalized)
        
        assert result.category == FailureCategory.UNKNOWN
        assert any("No specific error pattern" in ev for ev in result.evidence)
    
    def test_evidence_includes_locator_hints(self):
        """Test that evidence includes locator hints."""
        normalized = NormalizedFailure(
            raw_message="TimeoutError waiting for element",
            locator_hints=["text=Submit", "#btn-login"]
        )
        
        result = classify_failure(normalized)
        
        assert any("Locator hint" in ev for ev in result.evidence)
    
    def test_evidence_includes_step_info(self):
        """Test that evidence includes step information."""
        normalized = NormalizedFailure(
            raw_message="Error occurred",
            step="Click Submit Button"
        )
        
        result = classify_failure(normalized)
        
        assert any("Failed step" in ev for ev in result.evidence)
    
    def test_confidence_modifier_positive(self):
        """Test that clear matches increase confidence."""
        normalized = NormalizedFailure(
            raw_message="TimeoutError: Timeout 30000ms exceeded",
            step="Click button",
            locator_hints=["text=Submit"]
        )
        
        result = classify_failure(normalized)
        
        assert result.confidence_modifier > 0
    
    def test_confidence_modifier_negative_for_unknown(self):
        """Test that UNKNOWN category has negative confidence modifier."""
        normalized = NormalizedFailure(
            raw_message="Generic error with no specific pattern"
        )
        
        result = classify_failure(normalized)
        
        if result.category == FailureCategory.UNKNOWN:
            assert result.confidence_modifier < 0


class TestSampleFixtures:
    """Test classification of all sample fixtures."""
    
    @pytest.mark.parametrize("fixture_name", list(get_all_failure_fixtures().keys()))
    def test_fixture_classification(self, fixture_name):
        """Test that each fixture is classified as expected."""
        fixture = SAMPLE_FAILURES[fixture_name]
        expected = EXPECTED_CLASSIFICATIONS.get(fixture_name)
        
        # Skip if no expected classification defined
        if expected is None:
            pytest.skip(f"No expected classification for {fixture_name}")
        
        normalized = normalize_mcp_event(fixture)
        assert normalized is not None, f"Failed to normalize {fixture_name}"
        
        result = classify_failure(normalized)
        
        assert result.category.value == expected, \
            f"Expected {expected} for {fixture_name}, got {result.category.value}"


class TestClassificationRules:
    """Test individual classification rules."""
    
    def test_rules_are_defined(self):
        """Test that classification rules are defined."""
        assert len(CLASSIFICATION_RULES) >= 4
    
    def test_all_categories_have_rules(self):
        """Test that all non-UNKNOWN categories have rules."""
        categories_with_rules = set()
        for pattern, category, template in CLASSIFICATION_RULES:
            categories_with_rules.add(category)
        
        expected_categories = {
            FailureCategory.ELEMENT_NOT_FOUND,
            FailureCategory.ASSERTION_FAILED,
            FailureCategory.JS_ERROR,
            FailureCategory.NETWORK_FAILURE
        }
        
        assert expected_categories.issubset(categories_with_rules)


class TestGetCategoryDescription:
    """Tests for get_category_description function."""
    
    def test_all_categories_have_descriptions(self):
        """Test that all categories have descriptions."""
        for category in FailureCategory:
            description = get_category_description(category)
            assert description, f"No description for {category}"
            assert len(description) > 20, f"Description too short for {category}"
    
    def test_descriptions_are_helpful(self):
        """Test that descriptions contain helpful information."""
        desc = get_category_description(FailureCategory.ELEMENT_NOT_FOUND)
        assert "element" in desc.lower() or "selector" in desc.lower()
        
        desc = get_category_description(FailureCategory.NETWORK_FAILURE)
        assert "network" in desc.lower() or "server" in desc.lower()
