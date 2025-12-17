"""
Failure Analyzer Module

Analyzes test failures from Playwright MCP WebSocket events,
applies rule-based classification, and generates AI-powered explanations.

Usage:
    from failure_analyzer import FailureAnalyzer
    
    analyzer = FailureAnalyzer()  # Uses OpenAI
    # or
    analyzer = FailureAnalyzer(mock_openai=True)  # For testing
    
    result = await analyzer.analyze(raw_mcp_event)
"""

from .analyzer import FailureAnalyzer, analyze_failure
from .schemas import (
    FailureCategory,
    FailureAnalysis,
    NormalizedFailure,
    ClassificationResult,
    IgnoredEvent
)
from .normalizer import normalize_mcp_event, is_failure_event
from .classifier import classify_failure, get_category_description

__all__ = [
    # Main analyzer
    "FailureAnalyzer",
    "analyze_failure",
    # Schemas
    "FailureCategory",
    "FailureAnalysis",
    "NormalizedFailure",
    "ClassificationResult",
    "IgnoredEvent",
    # Utilities
    "normalize_mcp_event",
    "is_failure_event",
    "classify_failure",
    "get_category_description",
]
