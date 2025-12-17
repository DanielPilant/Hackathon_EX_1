"""
Rule-Based Failure Classifier

Classifies test failures into categories using deterministic regex patterns.
This runs before AI to improve accuracy and reduce hallucinations.
"""

import re
import logging
from typing import List, Tuple

from .schemas import NormalizedFailure, ClassificationResult, FailureCategory

logger = logging.getLogger(__name__)


# Classification rules: (pattern, category, evidence_template)
# Rules are checked in order - first match wins for category
CLASSIFICATION_RULES: List[Tuple[str, FailureCategory, str]] = [
    # ELEMENT_NOT_FOUND - Timeout and element issues
    (
        r"TimeoutError|Timeout\s*\d+ms\s*exceeded|waiting\s+for\s+locator|element\s+not\s+found|"
        r"no\s+element\s+matching|could\s+not\s+find\s+element|locator\s+resolved\s+to\s+\d+\s+elements?|"
        r"waiting\s+for\s+selector|selector\s+did\s+not\s+match",
        FailureCategory.ELEMENT_NOT_FOUND,
        "Timeout/element not found pattern matched: '{match}'"
    ),
    
    # ASSERTION_FAILED - Test assertions
    (
        r"AssertionError|expect\s*\(|\.toBe\(|\.toEqual\(|\.toContain\(|\.toMatch\(|"
        r"assertion\s+failed|expected\s+.*\s+to\s+(be|equal|match|contain)|"
        r"Expected:.*Received:|\.toHaveText\(|\.toBeVisible\(|\.toBeEnabled\(",
        FailureCategory.ASSERTION_FAILED,
        "Assertion failure pattern matched: '{match}'"
    ),
    
    # JS_ERROR - JavaScript runtime errors
    (
        r"TypeError|ReferenceError|SyntaxError|RangeError|URIError|EvalError|"
        r"Uncaught\s+\w+Error|undefined\s+is\s+not\s+a\s+function|"
        r"Cannot\s+read\s+propert(y|ies)\s+of\s+(undefined|null)|"
        r"is\s+not\s+a\s+function|is\s+not\s+defined|"
        r"Unexpected\s+token|Invalid\s+or\s+unexpected\s+token",
        FailureCategory.JS_ERROR,
        "JavaScript error pattern matched: '{match}'"
    ),
    
    # NETWORK_FAILURE - Network/HTTP errors
    (
        r"ERR_CONNECTION|ECONNREFUSED|ENOTFOUND|ETIMEDOUT|"
        r"net::|fetch\s+failed|network\s+error|"
        r"status\s*(code)?[:\s]*[45]\d{2}|"
        r"HTTP\s*[45]\d{2}|"
        r"Failed\s+to\s+fetch|NetworkError|"
        r"CORS|cross-origin|Access-Control-Allow",
        FailureCategory.NETWORK_FAILURE,
        "Network error pattern matched: '{match}'"
    ),
]

# Additional evidence patterns (not used for primary classification)
EVIDENCE_PATTERNS: List[Tuple[str, str]] = [
    (r"locator\(['\"]([^'\"]+)['\"]\)", "Locator used: {match}"),
    (r"text=([^\s'\"]+)", "Text selector: {match}"),
    (r"role=([^\s'\"]+)", "Role selector: {match}"),
    (r"#([a-zA-Z][a-zA-Z0-9_-]*)", "ID selector: #{match}"),
    (r"\.([a-zA-Z][a-zA-Z0-9_-]*)\b", "Class selector: .{match}"),
    (r"(\d+)\s*ms", "Timeout value: {match}ms"),
    (r"Expected:\s*['\"]?([^'\"]+)['\"]?", "Expected value: {match}"),
    (r"Received:\s*['\"]?([^'\"]+)['\"]?", "Received value: {match}"),
    (r"(https?://[^\s'\"]+)", "URL involved: {match}"),
    (r"status[:\s]*(\d{3})", "HTTP status: {match}"),
]


def classify_failure(normalized: NormalizedFailure) -> ClassificationResult:
    """
    Classify a failure using rule-based pattern matching.
    
    Args:
        normalized: Normalized failure data
        
    Returns:
        ClassificationResult with category and evidence
    """
    # Combine all text for pattern matching
    all_text = _combine_text_for_matching(normalized)
    
    # Find category using classification rules
    category = FailureCategory.UNKNOWN
    evidence: List[str] = []
    confidence_modifier = 0.0
    
    for pattern, rule_category, evidence_template in CLASSIFICATION_RULES:
        match = re.search(pattern, all_text, re.IGNORECASE)
        if match:
            category = rule_category
            matched_text = match.group(0)[:50]  # Truncate for readability
            evidence.append(evidence_template.format(match=matched_text))
            confidence_modifier += 0.2  # Boost confidence when rules match
            break  # First match wins for category
    
    # Gather additional evidence
    evidence.extend(_gather_evidence(all_text))
    
    # Add locator hints to evidence if present
    if normalized.locator_hints:
        for hint in normalized.locator_hints[:3]:  # Limit to first 3
            evidence.append(f"Locator hint: {hint}")
            confidence_modifier += 0.05
    
    # Add step info to evidence if present
    if normalized.step:
        evidence.append(f"Failed step: {normalized.step}")
        confidence_modifier += 0.1
    
    # Check for console errors
    if normalized.console_lines:
        for line in normalized.console_lines[:2]:
            if any(err in str(line).lower() for err in ["error", "exception", "failed"]):
                evidence.append(f"Console error: {str(line)[:60]}")
                confidence_modifier += 0.05
    
    # Check for network issues
    if normalized.network_lines:
        for net in normalized.network_lines[:2]:
            status = net.get("status", 0) if isinstance(net, dict) else 0
            if status >= 400:
                evidence.append(f"HTTP error status: {status}")
                if category == FailureCategory.UNKNOWN:
                    category = FailureCategory.NETWORK_FAILURE
                confidence_modifier += 0.1
    
    # Cap confidence modifier
    confidence_modifier = min(confidence_modifier, 0.4)
    
    # If still unknown, note that in evidence
    if category == FailureCategory.UNKNOWN:
        evidence.append("No specific error pattern matched")
        confidence_modifier = -0.2  # Reduce confidence for unknown
    
    return ClassificationResult(
        category=category,
        evidence=evidence,
        confidence_modifier=confidence_modifier
    )


def _combine_text_for_matching(normalized: NormalizedFailure) -> str:
    """Combine all available text for pattern matching."""
    parts = [
        normalized.raw_message,
        normalized.error_message or "",
        normalized.step or "",
    ]
    
    # Add console lines
    parts.extend(str(line) for line in normalized.console_lines)
    
    # Add network info
    for net in normalized.network_lines:
        if isinstance(net, dict):
            parts.append(str(net.get("url", "")))
            parts.append(str(net.get("status", "")))
            parts.append(str(net.get("error", "")))
        else:
            parts.append(str(net))
    
    return " ".join(parts)


def _gather_evidence(text: str) -> List[str]:
    """Extract additional evidence from text using patterns."""
    evidence = []
    seen = set()
    
    for pattern, template in EVIDENCE_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches[:2]:  # Limit matches per pattern
            if match not in seen:
                seen.add(match)
                evidence.append(template.format(match=match))
    
    return evidence[:10]  # Limit total evidence items


def get_category_description(category: FailureCategory) -> str:
    """Get human-readable description of a failure category."""
    descriptions = {
        FailureCategory.ELEMENT_NOT_FOUND: (
            "The test could not find or interact with an expected UI element. "
            "This typically happens when the element doesn't exist, hasn't loaded yet, "
            "or the selector is incorrect."
        ),
        FailureCategory.ASSERTION_FAILED: (
            "A test assertion failed - the actual value didn't match the expected value. "
            "This indicates the application behavior differs from what the test expected."
        ),
        FailureCategory.JS_ERROR: (
            "A JavaScript runtime error occurred in the browser. "
            "This could be a bug in the application code or an issue with the test script."
        ),
        FailureCategory.NETWORK_FAILURE: (
            "A network request failed or returned an error status. "
            "This could be a server error, connectivity issue, or CORS problem."
        ),
        FailureCategory.UNKNOWN: (
            "The failure type could not be automatically determined. "
            "Manual investigation of the error details is recommended."
        ),
    }
    return descriptions.get(category, "Unknown failure category")
