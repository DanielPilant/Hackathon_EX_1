"""
OpenAI Client for Failure Analysis

Handles communication with OpenAI API for generating failure explanations.
Includes rate limit handling and structured output enforcement.
"""

import os
import re
import json
import asyncio
import logging
from typing import Optional, Dict, Any

from openai import AsyncOpenAI, RateLimitError, APIError

from .schemas import NormalizedFailure, ClassificationResult, FAILURE_ANALYSIS_JSON_SCHEMA
from .prompts import SYSTEM_PROMPT, build_analysis_prompt, build_fallback_response

logger = logging.getLogger(__name__)

# Default model - matches MCP_Agent configuration
DEFAULT_MODEL = "gpt-4o-mini"


class OpenAIAnalysisClient:
    """
    Client for generating AI-powered failure analysis using OpenAI.
    
    Supports:
    - Structured JSON output
    - Rate limit handling with retries
    - Mock mode for testing without API calls
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        mock_mode: bool = False,
        max_retries: int = 3
    ):
        """
        Initialize the OpenAI client.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model to use for analysis
            mock_mode: If True, return mock responses without API calls
            max_retries: Maximum retries on rate limit errors
        """
        self.model = model
        self.mock_mode = mock_mode
        self.max_retries = max_retries
        
        if not mock_mode:
            self.client = AsyncOpenAI(
                api_key=api_key or os.getenv("OPENAI_API_KEY")
            )
        else:
            self.client = None
    
    async def generate_analysis(
        self,
        normalized: NormalizedFailure,
        classification: ClassificationResult
    ) -> Dict[str, Any]:
        """
        Generate AI analysis for a failure.
        
        Args:
            normalized: Normalized failure data
            classification: Rule-based classification result
            
        Returns:
            Dict with summary, why, suggested_fix, confidence
        """
        if self.mock_mode:
            return self._mock_response(normalized, classification)
        
        try:
            return await self._call_openai_with_retry(normalized, classification)
        except Exception as e:
            logger.error(f"OpenAI analysis failed: {e}")
            # Return fallback response on error
            return build_fallback_response(normalized, classification)
    
    async def _call_openai_with_retry(
        self,
        normalized: NormalizedFailure,
        classification: ClassificationResult
    ) -> Dict[str, Any]:
        """
        Call OpenAI with retry logic for rate limits.
        """
        user_prompt = build_analysis_prompt(normalized, classification)
        
        for attempt in range(1, self.max_retries + 1):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.3,  # Lower temperature for more consistent output
                    max_tokens=500
                )
                
                # Parse response
                content = response.choices[0].message.content
                return self._parse_response(content, classification)
                
            except RateLimitError as e:
                retry_after = self._parse_retry_after(str(e))
                if retry_after and attempt < self.max_retries:
                    logger.warning(f"Rate limited, waiting {retry_after}s (attempt {attempt})")
                    await asyncio.sleep(retry_after + 0.5)
                    continue
                elif attempt < self.max_retries:
                    wait_time = min(2 ** attempt, 10)
                    logger.warning(f"Rate limited, waiting {wait_time}s (attempt {attempt})")
                    await asyncio.sleep(wait_time)
                    continue
                raise
                
            except APIError as e:
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt
                    logger.warning(f"API error, retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                    continue
                raise
        
        # Should not reach here, but fallback just in case
        return build_fallback_response(normalized, classification)
    
    def _parse_response(
        self,
        content: str,
        classification: ClassificationResult
    ) -> Dict[str, Any]:
        """
        Parse and validate OpenAI response.
        """
        try:
            data = json.loads(content)
            
            # Validate required fields
            result = {
                "summary": str(data.get("summary", "Analysis unavailable")),
                "why": str(data.get("why", "No explanation provided")),
                "suggested_fix": str(data.get("suggested_fix", "Review error logs")),
                "confidence": float(data.get("confidence", 0.5))
            }
            
            # Adjust confidence based on classification
            result["confidence"] = min(1.0, max(0.0, 
                result["confidence"] + classification.confidence_modifier
            ))
            result["confidence"] = round(result["confidence"], 2)
            
            return result
            
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.error(f"Failed to parse OpenAI response: {e}")
            logger.debug(f"Raw response: {content[:500]}")
            
            # Try to extract useful info from malformed response
            return self._extract_from_text(content, classification)
    
    def _extract_from_text(
        self,
        content: str,
        classification: ClassificationResult
    ) -> Dict[str, Any]:
        """
        Try to extract useful information from non-JSON response.
        """
        # Simple extraction using patterns
        summary = ""
        why = ""
        fix = ""
        
        # Try to find summary-like content
        if "summary" in content.lower():
            match = re.search(r'"?summary"?\s*[:=]\s*"?([^"}\n]+)', content, re.IGNORECASE)
            if match:
                summary = match.group(1).strip()
        
        if not summary:
            # Take first sentence as summary
            sentences = content.split(".")
            if sentences:
                summary = sentences[0].strip()[:200]
        
        # Try to find fix suggestion
        if "fix" in content.lower() or "suggest" in content.lower():
            match = re.search(r'"?suggested?_?fix"?\s*[:=]\s*"?([^"}\n]+)', content, re.IGNORECASE)
            if match:
                fix = match.group(1).strip()
        
        return {
            "summary": summary or "Could not generate summary",
            "why": why or content[:300],
            "suggested_fix": fix or "Review error logs for more details",
            "confidence": 0.3 + classification.confidence_modifier
        }
    
    def _parse_retry_after(self, error_msg: str) -> Optional[float]:
        """Extract retry-after seconds from rate limit error message."""
        match = re.search(r"Please try again in ([0-9.]+)s", error_msg)
        return float(match.group(1)) if match else None
    
    def _mock_response(
        self,
        normalized: NormalizedFailure,
        classification: ClassificationResult
    ) -> Dict[str, Any]:
        """
        Generate mock response for testing.
        """
        category = classification.category.value
        step = normalized.step or "unknown step"
        
        mock_responses = {
            "ELEMENT_NOT_FOUND": {
                "summary": f"The test failed because the target element was not found during '{step}'.",
                "why": f"Playwright waited for the element but it never appeared. "
                       f"Evidence: {'; '.join(classification.evidence[:2])}",
                "suggested_fix": "Verify the selector matches an existing element or add explicit waits.",
                "confidence": 0.82
            },
            "ASSERTION_FAILED": {
                "summary": f"An assertion failed during '{step}' - expected value did not match actual.",
                "why": f"The test expected a specific value but received something different. "
                       f"Evidence: {'; '.join(classification.evidence[:2])}",
                "suggested_fix": "Review the expected value and verify the application behavior.",
                "confidence": 0.78
            },
            "JS_ERROR": {
                "summary": f"A JavaScript error occurred during '{step}'.",
                "why": f"The browser encountered a runtime JavaScript error. "
                       f"Evidence: {'; '.join(classification.evidence[:2])}",
                "suggested_fix": "Check the browser console and application code for bugs.",
                "confidence": 0.75
            },
            "NETWORK_FAILURE": {
                "summary": f"A network request failed during '{step}'.",
                "why": f"An HTTP request failed or returned an error. "
                       f"Evidence: {'; '.join(classification.evidence[:2])}",
                "suggested_fix": "Verify the server is accessible and the API endpoint is correct.",
                "confidence": 0.80
            },
            "UNKNOWN": {
                "summary": f"The test failed during '{step}' for an undetermined reason.",
                "why": f"Could not automatically determine the failure cause. "
                       f"Raw error: {normalized.raw_message[:100]}",
                "suggested_fix": "Review the full error logs for more context.",
                "confidence": 0.35
            }
        }
        
        response = mock_responses.get(category, mock_responses["UNKNOWN"])
        
        # Adjust confidence with classification modifier
        response["confidence"] = min(1.0, max(0.0,
            response["confidence"] + classification.confidence_modifier
        ))
        response["confidence"] = round(response["confidence"], 2)
        
        return response
