"""
Normalizer for MCP Event Data

Flexible extraction layer that handles evolving JSON formats from Playwright MCP.
Safely extracts fields even when structure changes.
"""

import re
import logging
from typing import Optional, Dict, Any, List

from .schemas import NormalizedFailure

logger = logging.getLogger(__name__)

# Possible field names for each data type (handles format evolution)
MESSAGE_FIELDS = ["message", "msg", "error", "errorMessage", "error_message", "text", "data"]
STEP_FIELDS = ["step", "stepName", "step_name", "description", "action", "name"]
CONSOLE_FIELDS = ["console", "consoleLogs", "console_logs", "logs"]
NETWORK_FIELDS = ["network", "networkLogs", "network_logs", "requests", "responses"]

# Regex patterns to extract locator hints from error messages
LOCATOR_PATTERNS = [
    r'locator\(["\']([^"\']+)["\']\)',  # locator("text=Submit")
    r'locator\s*=\s*["\']([^"\']+)["\']',  # locator = "text=Submit"
    r'text=([^\s"\']+)',  # text=Submit
    r'role=([^\s"\']+)',  # role=button
    r'selector[:\s]+["\']?([^"\'>\s]+)',  # selector: ".btn"
    r'#([a-zA-Z][a-zA-Z0-9_-]*)',  # #elementId
    r'\.([a-zA-Z][a-zA-Z0-9_-]*)',  # .className (first occurrence)
    r'\[data-testid=["\']([^"\']+)["\']\]',  # [data-testid="submit"]
]


def _deep_get(data: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    """
    Recursively search for a key in nested dictionaries.
    Returns the first match found.
    """
    if not isinstance(data, dict):
        return default
    
    for key in keys:
        if key in data:
            return data[key]
    
    # Search in nested objects
    for value in data.values():
        if isinstance(value, dict):
            result = _deep_get(value, keys, None)
            if result is not None:
                return result
    
    return default


def _extract_string(data: Dict[str, Any], field_names: List[str]) -> str:
    """Extract a string value from data, trying multiple field names."""
    value = _deep_get(data, field_names)
    
    if value is None:
        return ""
    
    if isinstance(value, str):
        return value
    
    if isinstance(value, (list, tuple)) and value:
        return str(value[0])
    
    return str(value)


def _extract_list(data: Dict[str, Any], field_names: List[str]) -> List[Any]:
    """Extract a list value from data, trying multiple field names."""
    value = _deep_get(data, field_names)
    
    if value is None:
        return []
    
    if isinstance(value, list):
        return value
    
    if isinstance(value, str):
        return [value] if value else []
    
    return [value]


def _extract_locator_hints(text: str) -> List[str]:
    """Extract locator/selector hints from error message text."""
    hints = []
    
    for pattern in LOCATOR_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        hints.extend(matches)
    
    # Deduplicate while preserving order
    seen = set()
    unique_hints = []
    for hint in hints:
        if hint and hint not in seen:
            seen.add(hint)
            unique_hints.append(hint)
    
    return unique_hints


def _flatten_event(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Flatten nested event structures to make field extraction easier.
    Handles formats like: {"payload": {...}}, {"data": {...}}, {"event": {...}}
    """
    flattened = dict(data)
    
    # Common wrapper keys to unwrap
    wrappers = ["payload", "data", "event", "error", "result"]
    
    for wrapper in wrappers:
        if wrapper in data and isinstance(data[wrapper], dict):
            # Merge nested dict into flattened, but don't overwrite existing keys
            for key, value in data[wrapper].items():
                if key not in flattened:
                    flattened[key] = value
    
    return flattened


def normalize_mcp_event(raw_event: Dict[str, Any]) -> Optional[NormalizedFailure]:
    """
    Extract normalized failure data from evolving MCP JSON format.
    
    Args:
        raw_event: Raw JSON event from MCP WebSocket
        
    Returns:
        NormalizedFailure object, or None if extraction fails completely
    """
    if not raw_event or not isinstance(raw_event, dict):
        logger.warning("normalize_mcp_event received invalid input")
        return None
    
    try:
        # Flatten nested structures
        flat = _flatten_event(raw_event)
        
        # Extract message (most important field)
        raw_message = _extract_string(flat, MESSAGE_FIELDS)
        
        # If no message found, try to build one from the entire event
        if not raw_message:
            # Check if the whole event is a string-like error
            if "type" in raw_event and raw_event.get("type") in ("error", "log"):
                raw_message = str(raw_event)
        
        # Extract step name
        step = _extract_string(flat, STEP_FIELDS) or None
        
        # Extract console logs
        console_lines = _extract_list(flat, CONSOLE_FIELDS)
        # Ensure all items are strings
        console_lines = [str(item) for item in console_lines if item]
        
        # Extract network logs
        network_lines = _extract_list(flat, NETWORK_FIELDS)
        # Ensure all items are dicts or convert
        network_lines = [
            item if isinstance(item, dict) else {"raw": str(item)}
            for item in network_lines if item
        ]
        
        # Extract locator hints from message
        locator_hints = _extract_locator_hints(raw_message)
        
        # Also check console logs for locator hints
        for line in console_lines:
            locator_hints.extend(_extract_locator_hints(str(line)))
        
        # Deduplicate locator hints
        locator_hints = list(dict.fromkeys(locator_hints))
        
        return NormalizedFailure(
            raw_message=raw_message,
            step=step,
            error_message=raw_message,  # Alias for convenience
            console_lines=console_lines,
            network_lines=network_lines,
            locator_hints=locator_hints,
            raw_event=raw_event
        )
        
    except Exception as e:
        logger.error(f"Error normalizing MCP event: {e}")
        # Return minimal normalized object
        return NormalizedFailure(
            raw_message=str(raw_event),
            raw_event=raw_event
        )


def is_failure_event(raw_event: Dict[str, Any]) -> bool:
    """
    Check if an event represents a failure that should be analyzed.
    
    Args:
        raw_event: Raw JSON event from MCP WebSocket
        
    Returns:
        True if this event should trigger failure analysis
    """
    if not raw_event or not isinstance(raw_event, dict):
        return False
    
    flat = _flatten_event(raw_event)
    
    # Check event type
    event_type = flat.get("type", "").lower()
    if event_type in ("error", "fail", "failure"):
        return True
    
    # Check log level
    level = flat.get("level", "").lower()
    if level in ("error", "fatal", "critical"):
        return True
    
    # Check message content for error indicators
    message = _extract_string(flat, MESSAGE_FIELDS).lower()
    error_indicators = [
        "error", "timeout", "failed", "exception", 
        "assertionerror", "typeerror", "referenceerror",
        "err_connection", "econnrefused", "unexpected",
        "404", "500", "403", "401", "not found", "forbidden"
    ]
    
    for indicator in error_indicators:
        if indicator in message:
            return True
    
    # Check for status field indicating failure
    status = flat.get("status", "").lower()
    if status in ("fail", "failed", "error"):
        return True
    
    return False
