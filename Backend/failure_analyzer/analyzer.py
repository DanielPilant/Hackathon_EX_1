"""
Main Failure Analyzer

Orchestrates the failure analysis pipeline:
1. Normalize raw MCP events
2. Classify using rules
3. Generate AI explanation
4. Return structured analysis
"""

import logging
from typing import Dict, Any, Optional

from .schemas import (
    FailureAnalysis,
    IgnoredEvent,
    NormalizedFailure,
    ClassificationResult,
    FailureCategory
)
from .normalizer import normalize_mcp_event, is_failure_event
from .classifier import classify_failure
from .openai_client import OpenAIAnalysisClient

logger = logging.getLogger(__name__)


class FailureAnalyzer:
    """
    Main class for analyzing test failures from MCP events.
    
    Usage:
        analyzer = FailureAnalyzer()
        result = await analyzer.analyze(raw_event)
        
    For testing without OpenAI:
        analyzer = FailureAnalyzer(mock_openai=True)
    """
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        openai_model: str = "gpt-4o-mini",
        mock_openai: bool = False
    ):
        """
        Initialize the failure analyzer.
        
        Args:
            openai_api_key: Optional API key (defaults to env var)
            openai_model: OpenAI model to use
            mock_openai: If True, use mock responses instead of real API
        """
        self.openai_client = OpenAIAnalysisClient(
            api_key=openai_api_key,
            model=openai_model,
            mock_mode=mock_openai
        )
        self.mock_mode = mock_openai
        logger.info(f"FailureAnalyzer initialized (mock_mode={mock_openai})")
    
    async def analyze(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a raw MCP event for failures.
        
        This is the main entry point. It:
        1. Checks if the event is a failure
        2. Normalizes the data
        3. Classifies using rules
        4. Generates AI explanation
        5. Returns structured analysis
        
        Args:
            raw_event: Raw JSON event from MCP WebSocket
            
        Returns:
            FailureAnalysis dict if failure detected,
            IgnoredEvent dict if not a failure
        """
        # Step 1: Check if this is a failure event
        if not is_failure_event(raw_event):
            logger.debug("Event is not a failure, ignoring")
            return IgnoredEvent().model_dump()
        
        logger.info("Failure event detected, starting analysis")
        
        try:
            # Step 2: Normalize the event
            normalized = normalize_mcp_event(raw_event)
            if normalized is None:
                logger.warning("Failed to normalize event")
                return self._create_minimal_analysis(raw_event)
            
            logger.debug(f"Normalized event: step={normalized.step}, "
                        f"locators={normalized.locator_hints}")
            
            # Step 3: Classify using rules
            classification = classify_failure(normalized)
            logger.info(f"Classified as: {classification.category.value} "
                       f"(evidence: {len(classification.evidence)} items)")
            
            # Step 4: Generate AI explanation
            ai_response = await self.openai_client.generate_analysis(
                normalized, classification
            )
            
            # Step 5: Build final analysis
            analysis = FailureAnalysis(
                failed_step=normalized.step,
                failure_category=classification.category,
                summary=ai_response["summary"],
                why=ai_response["why"],
                evidence=classification.evidence,
                suggested_fix=ai_response["suggested_fix"],
                confidence=ai_response["confidence"]
            )
            
            logger.info(f"Analysis complete: {analysis.failure_category} "
                       f"(confidence: {analysis.confidence})")
            
            return analysis.model_dump()
            
        except Exception as e:
            logger.error(f"Error during analysis: {e}", exc_info=True)
            return self._create_error_analysis(raw_event, str(e))
    
    def analyze_sync(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synchronous wrapper for analyze().
        
        Useful for testing or non-async contexts.
        """
        import asyncio
        return asyncio.run(self.analyze(raw_event))
    
    async def analyze_batch(
        self,
        events: list[Dict[str, Any]]
    ) -> list[Dict[str, Any]]:
        """
        Analyze multiple events.
        
        Args:
            events: List of raw MCP events
            
        Returns:
            List of analysis results
        """
        results = []
        for event in events:
            result = await self.analyze(event)
            results.append(result)
        return results
    
    def _create_minimal_analysis(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        """Create minimal analysis when normalization fails."""
        return FailureAnalysis(
            failure_category=FailureCategory.UNKNOWN,
            summary="Could not analyze failure - normalization failed",
            why=f"Raw event: {str(raw_event)[:200]}",
            evidence=["Normalization failed"],
            suggested_fix="Review raw event data manually",
            confidence=0.1
        ).model_dump()
    
    def _create_error_analysis(
        self,
        raw_event: Dict[str, Any],
        error_msg: str
    ) -> Dict[str, Any]:
        """Create analysis when an error occurs during processing."""
        return FailureAnalysis(
            failure_category=FailureCategory.UNKNOWN,
            summary="Error occurred during failure analysis",
            why=f"Analysis error: {error_msg}",
            evidence=[f"Processing error: {error_msg}"],
            suggested_fix="Check analyzer logs and retry",
            confidence=0.0
        ).model_dump()


# Convenience function for quick analysis
async def analyze_failure(
    raw_event: Dict[str, Any],
    mock: bool = False
) -> Dict[str, Any]:
    """
    Quick function to analyze a single failure event.
    
    Args:
        raw_event: Raw MCP event
        mock: If True, use mock OpenAI responses
        
    Returns:
        Analysis result dict
    """
    analyzer = FailureAnalyzer(mock_openai=mock)
    return await analyzer.analyze(raw_event)
