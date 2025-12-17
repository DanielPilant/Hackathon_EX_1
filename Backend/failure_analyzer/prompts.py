"""
OpenAI Prompt Templates for Failure Analysis

Contains the system prompt and formatting functions for generating
AI-powered failure explanations.
"""

from typing import List
from .schemas import NormalizedFailure, ClassificationResult, FailureCategory


SYSTEM_PROMPT = """You are a senior QA automation engineer specializing in Playwright test debugging.

Your task is to analyze test failure data and provide:
1. A clear, concise summary of why the test failed
2. A detailed explanation based ONLY on the evidence provided
3. One concrete, actionable fix suggestion

IMPORTANT RULES:
- Base your analysis ONLY on the provided data - do not make assumptions
- Keep the summary to 1-2 sentences
- The "why" explanation should reference specific evidence
- Suggest only ONE fix, make it specific and actionable
- If data is insufficient, acknowledge uncertainty and lower your confidence
- Confidence should reflect how certain you are based on available evidence

OUTPUT FORMAT:
You must respond with valid JSON matching this schema:
{
    "summary": "Short human-readable reason (1-2 sentences)",
    "why": "Detailed explanation referencing evidence",
    "suggested_fix": "Single actionable suggestion",
    "confidence": 0.0 to 1.0
}"""


def build_analysis_prompt(
    normalized: NormalizedFailure,
    classification: ClassificationResult
) -> str:
    """
    Build the user prompt for OpenAI analysis.
    
    Args:
        normalized: Normalized failure data
        classification: Rule-based classification result
        
    Returns:
        Formatted prompt string
    """
    parts = []
    
    # Header
    parts.append("Analyze this test failure:\n")
    
    # Classification info
    parts.append(f"**Pre-classified Category:** {classification.category.value}")
    parts.append(f"**Category Description:** {_get_category_hint(classification.category)}\n")
    
    # Error message
    if normalized.raw_message:
        parts.append(f"**Error Message:**\n```\n{normalized.raw_message[:1000]}\n```\n")
    
    # Failed step
    if normalized.step:
        parts.append(f"**Failed Step:** {normalized.step}\n")
    
    # Locator hints
    if normalized.locator_hints:
        parts.append(f"**Locators Involved:** {', '.join(normalized.locator_hints[:5])}\n")
    
    # Evidence from classifier
    if classification.evidence:
        parts.append("**Evidence Detected:**")
        for ev in classification.evidence[:8]:
            parts.append(f"  - {ev}")
        parts.append("")
    
    # Console logs
    if normalized.console_lines:
        parts.append("**Console Logs:**")
        for line in normalized.console_lines[:5]:
            parts.append(f"  - {str(line)[:200]}")
        parts.append("")
    
    # Network info
    if normalized.network_lines:
        parts.append("**Network Activity:**")
        for net in normalized.network_lines[:3]:
            if isinstance(net, dict):
                url = net.get("url", "")[:100]
                status = net.get("status", "")
                parts.append(f"  - {url} (status: {status})")
            else:
                parts.append(f"  - {str(net)[:100]}")
        parts.append("")
    
    # Instructions
    parts.append("Based on this data, provide your analysis as JSON.")
    
    return "\n".join(parts)


def _get_category_hint(category: FailureCategory) -> str:
    """Get a hint for the AI about what to focus on for each category."""
    hints = {
        FailureCategory.ELEMENT_NOT_FOUND: (
            "Focus on selector/locator issues, page load timing, or missing elements"
        ),
        FailureCategory.ASSERTION_FAILED: (
            "Focus on the expected vs actual values and why they might differ"
        ),
        FailureCategory.JS_ERROR: (
            "Focus on the JavaScript error type and what might have caused it"
        ),
        FailureCategory.NETWORK_FAILURE: (
            "Focus on the network request that failed and potential server/connectivity issues"
        ),
        FailureCategory.UNKNOWN: (
            "Analyze all available data to determine the most likely cause"
        ),
    }
    return hints.get(category, "Analyze the error carefully")


def build_fallback_response(
    normalized: NormalizedFailure,
    classification: ClassificationResult
) -> dict:
    """
    Build a fallback response when OpenAI is unavailable or fails.
    Uses rule-based classification data to generate a basic analysis.
    
    Args:
        normalized: Normalized failure data
        classification: Rule-based classification result
        
    Returns:
        Dict matching FailureAnalysis schema
    """
    category = classification.category
    
    # Build summary based on category
    summaries = {
        FailureCategory.ELEMENT_NOT_FOUND: (
            f"The test failed because an element could not be found or interacted with"
            f"{f' in step: {normalized.step}' if normalized.step else ''}."
        ),
        FailureCategory.ASSERTION_FAILED: (
            "The test failed because an assertion did not match the expected value."
        ),
        FailureCategory.JS_ERROR: (
            "The test failed due to a JavaScript error in the browser."
        ),
        FailureCategory.NETWORK_FAILURE: (
            "The test failed due to a network error or failed HTTP request."
        ),
        FailureCategory.UNKNOWN: (
            "The test failed but the exact cause could not be automatically determined."
        ),
    }
    
    # Build why explanation
    why_parts = [f"Category: {category.value}"]
    if normalized.raw_message:
        why_parts.append(f"Error: {normalized.raw_message[:200]}")
    if classification.evidence:
        why_parts.append(f"Evidence: {'; '.join(classification.evidence[:3])}")
    
    # Build suggested fix based on category
    fixes = {
        FailureCategory.ELEMENT_NOT_FOUND: (
            "Verify the element exists on the page and update the selector if needed. "
            "Consider adding explicit waits or checking for dynamic content."
        ),
        FailureCategory.ASSERTION_FAILED: (
            "Review the expected value in the assertion and verify it matches "
            "the actual application behavior."
        ),
        FailureCategory.JS_ERROR: (
            "Check the browser console for the full error stack trace and "
            "review the application code for bugs."
        ),
        FailureCategory.NETWORK_FAILURE: (
            "Verify the server is running and accessible. Check for CORS issues "
            "or API endpoint changes."
        ),
        FailureCategory.UNKNOWN: (
            "Review the raw error logs for more context and check recent code changes."
        ),
    }
    
    # Calculate confidence (lower for fallback)
    confidence = 0.4 + classification.confidence_modifier
    confidence = max(0.1, min(0.6, confidence))  # Cap between 0.1 and 0.6
    
    return {
        "summary": summaries.get(category, "Test failure occurred."),
        "why": " | ".join(why_parts),
        "suggested_fix": fixes.get(category, "Review the error logs for more details."),
        "confidence": round(confidence, 2)
    }
