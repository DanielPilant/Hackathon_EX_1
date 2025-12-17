"""
Pydantic Schemas for Failure Analyzer

Defines data models for:
- NormalizedFailure: Intermediate normalized structure from raw MCP events
- FailureAnalysis: Final structured analysis output
- FailureCategory: Classification categories for failures
"""

import uuid
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class FailureCategory(str, Enum):
    """Classification categories for test failures."""
    ELEMENT_NOT_FOUND = "ELEMENT_NOT_FOUND"
    ASSERTION_FAILED = "ASSERTION_FAILED"
    JS_ERROR = "JS_ERROR"
    NETWORK_FAILURE = "NETWORK_FAILURE"
    UNKNOWN = "UNKNOWN"


class NormalizedFailure(BaseModel):
    """
    Intermediate normalized structure extracted from raw MCP JSON.
    
    This structure is flexible and handles missing fields gracefully.
    """
    raw_message: str = Field(default="", description="The raw error message")
    step: Optional[str] = Field(default=None, description="The step/description where failure occurred")
    error_message: Optional[str] = Field(default=None, description="Extracted error message")
    console_lines: List[str] = Field(default_factory=list, description="Console log entries")
    network_lines: List[Dict[str, Any]] = Field(default_factory=list, description="Network log entries")
    locator_hints: List[str] = Field(default_factory=list, description="Extracted locator/selector hints")
    raw_event: Dict[str, Any] = Field(default_factory=dict, description="Original raw event for reference")
    
    model_config = {"extra": "allow"}  # Allow extra fields for flexibility


class ClassificationResult(BaseModel):
    """Result of rule-based classification."""
    category: FailureCategory = Field(default=FailureCategory.UNKNOWN)
    evidence: List[str] = Field(default_factory=list, description="Evidence/reasons for classification")
    confidence_modifier: float = Field(default=0.0, description="Modifier to adjust AI confidence")


class FailureAnalysis(BaseModel):
    """
    Final structured analysis output.
    
    This is the schema that will be sent via WebSocket to the frontend.
    """
    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    failed_step: Optional[str] = Field(default=None, description="The step where failure occurred")
    failure_category: FailureCategory = Field(default=FailureCategory.UNKNOWN)
    summary: str = Field(default="", description="Short human-readable summary")
    why: str = Field(default="", description="Detailed explanation based on evidence")
    evidence: List[str] = Field(default_factory=list, description="Key facts/detections")
    suggested_fix: str = Field(default="", description="Single actionable suggestion")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Confidence score 0-1")
    
    model_config = {"use_enum_values": True}  # Serialize enum as string values


class IgnoredEvent(BaseModel):
    """Response for non-failure events that are ignored."""
    status: str = Field(default="ignored_non_failure_log")


# OpenAI structured output schema (for response_format)
FAILURE_ANALYSIS_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "string",
            "description": "Short human-readable reason for the failure"
        },
        "why": {
            "type": "string", 
            "description": "More detailed explanation based only on evidence"
        },
        "suggested_fix": {
            "type": "string",
            "description": "A single actionable suggestion to fix the issue"
        },
        "confidence": {
            "type": "number",
            "description": "Confidence score between 0 and 1"
        }
    },
    "required": ["summary", "why", "suggested_fix", "confidence"],
    "additionalProperties": False
}
