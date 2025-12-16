import json
from typing import Dict, Any

def extract_json_from_response(raw_response: str, expected_key: str = "plan") -> Dict[str, Any]:
    """
    Extracts and validates JSON from a raw string response (typically from an LLM).

    Args:
        raw_response (str): The raw string response which may contain markdown code blocks.
        expected_key (str): The key expected to be present in the JSON dictionary. Defaults to "plan".

    Returns:
        Dict[str, Any]: The parsed and validated JSON dictionary.

    Raises:
        ValueError: If the response is not valid JSON or fails validation checks.
    """
    text = raw_response.strip()

    # Remove markdown code blocks
    if text.lower().startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    
    if text.endswith("```"):
        text = text[:-3]
    
    text = text.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON response from AI model")

    # Validation
    if not isinstance(data, dict):
        raise ValueError("Response must be a dictionary")
    
    if expected_key not in data:
        raise ValueError(f"Response missing required '{expected_key}' key")
    
    if not isinstance(data[expected_key], list):
        raise ValueError(f"'{expected_key}' must be a list")
    
    if not data[expected_key]:
        raise ValueError(f"'{expected_key}' cannot be empty")

    return data
