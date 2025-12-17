# Failure Analyzer Module

A backend module that analyzes test failures from Playwright MCP WebSocket events, applies rule-based classification, and generates AI-powered explanations with suggested fixes.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage Guide](#usage-guide)
  - [Programmatic Usage](#programmatic-usage)
  - [CLI Testing Tool](#cli-testing-tool)
  - [WebSocket Integration](#websocket-integration)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Extending the Module](#extending-the-module)
- [Common Pitfalls](#common-pitfalls)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

---

## Overview

The Failure Analyzer intercepts test execution events, identifies failures, and produces structured JSON analysis explaining:
- **What** failed (category classification)
- **Why** it failed (evidence-based explanation)
- **How** to fix it (actionable suggestion)

### Key Features

- **Flexible Normalization**: Handles evolving MCP JSON formats without breaking
- **Rule-Based Classification**: Deterministic classification before AI (reduces hallucinations)
- **AI-Powered Explanations**: Uses OpenAI for human-readable summaries
- **Mock Mode**: Full testing capability without API calls
- **WebSocket Integration**: Real-time failure analysis streaming

### Failure Categories

| Category | Description | Example Triggers |
|----------|-------------|------------------|
| `ELEMENT_NOT_FOUND` | Element/selector issues | TimeoutError, locator not found |
| `ASSERTION_FAILED` | Test assertions failed | expect().toBe(), AssertionError |
| `JS_ERROR` | JavaScript runtime errors | TypeError, ReferenceError |
| `NETWORK_FAILURE` | HTTP/network issues | ERR_CONNECTION, HTTP 4xx/5xx |
| `UNKNOWN` | Unclassified failures | Generic errors |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Agent Server                          │
│                  (MCP_Agent/server.py)                       │
└──────────────────────┬──────────────────────────────────────┘
                       │ WebSocket Events
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   Failure Analyzer                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Normalizer │→ │ Classifier  │→ │   OpenAI Client     │  │
│  │             │  │ (Rule-Based)│  │ (AI Explanation)    │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │ Structured JSON
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                      Frontend                                │
│              (WebSocket Consumer)                            │
└─────────────────────────────────────────────────────────────┘
```

### Module Structure

```
failure_analyzer/
├── __init__.py          # Public exports
├── analyzer.py          # Main FailureAnalyzer class
├── normalizer.py        # JSON normalization layer
├── classifier.py        # Rule-based classification
├── openai_client.py     # OpenAI API integration
├── prompts.py           # AI prompt templates
├── schemas.py           # Pydantic data models
├── test_fixtures.py     # Sample test data
├── test_cli.py          # CLI testing tool
├── pytest.ini           # Test configuration
├── README.md            # This file
└── tests/
    ├── __init__.py
    ├── conftest.py      # Pytest fixtures
    ├── test_analyzer.py
    ├── test_classifier.py
    └── test_normalizer.py
```

---

## Installation

### Dependencies

The module requires these packages (add to your `requirements.txt`):

```
openai>=1.0.0
pydantic>=2.0.0
python-dotenv>=1.0.0

# For testing
pytest>=7.0.0
pytest-asyncio>=0.21.0
```

### Environment Variables

```bash
# Required for real OpenAI calls
OPENAI_API_KEY=sk-your-api-key-here

# Optional: Override default model
OPENAI_MODEL=gpt-4o-mini  # Default
```

---

## Quick Start

### 1. Basic Usage (Mock Mode - No API Key Needed)

```python
import asyncio
from failure_analyzer import FailureAnalyzer

async def main():
    # Create analyzer in mock mode (no OpenAI calls)
    analyzer = FailureAnalyzer(mock_openai=True)
    
    # Sample failure event
    event = {
        "type": "error",
        "payload": {
            "message": "TimeoutError: Timeout 30000ms exceeded waiting for locator(\"text=Submit\")",
            "stepName": "Click Submit button"
        }
    }
    
    # Analyze
    result = await analyzer.analyze(event)
    print(result)

asyncio.run(main())
```

### 2. With Real OpenAI

```python
analyzer = FailureAnalyzer()  # Uses OPENAI_API_KEY from env
result = await analyzer.analyze(event)
```

### 3. CLI Quick Test

```bash
cd Backend
python -m failure_analyzer.test_cli --fixture timeout_error --no-ai
```

---

## Usage Guide

### Programmatic Usage

#### Initialize the Analyzer

```python
from failure_analyzer import FailureAnalyzer

# Option 1: Production mode (real OpenAI)
analyzer = FailureAnalyzer()

# Option 2: Testing mode (mock responses)
analyzer = FailureAnalyzer(mock_openai=True)

# Option 3: Custom configuration
analyzer = FailureAnalyzer(
    openai_api_key="sk-custom-key",  # Override env var
    openai_model="gpt-4o",           # Use different model
    mock_openai=False
)
```

#### Analyze Events

```python
# Async usage (recommended)
result = await analyzer.analyze(raw_event)

# Sync usage (for scripts/testing)
result = analyzer.analyze_sync(raw_event)

# Batch analysis
results = await analyzer.analyze_batch([event1, event2, event3])
```

#### Check if Event is a Failure

```python
from failure_analyzer import is_failure_event

if is_failure_event(raw_event):
    result = await analyzer.analyze(raw_event)
```

#### Access Individual Components

```python
from failure_analyzer import (
    normalize_mcp_event,
    classify_failure,
    is_failure_event
)

# Step 1: Normalize
normalized = normalize_mcp_event(raw_event)

# Step 2: Classify (rule-based)
classification = classify_failure(normalized)
print(f"Category: {classification.category}")
print(f"Evidence: {classification.evidence}")

# Step 3: Full analysis (includes AI)
result = await analyzer.analyze(raw_event)
```

### CLI Testing Tool

The CLI allows testing without running the full MCP server.

```bash
# List all available test fixtures
python -m failure_analyzer.test_cli --list

# Test specific fixture (mock mode)
python -m failure_analyzer.test_cli --fixture timeout_error --no-ai

# Test specific fixture (real OpenAI)
python -m failure_analyzer.test_cli --fixture timeout_error

# Test custom JSON
python -m failure_analyzer.test_cli --json '{"type":"error","message":"TimeoutError"}'

# Test from file
python -m failure_analyzer.test_cli --file my_error.json

# Run all fixtures
python -m failure_analyzer.test_cli --no-ai

# Verbose output
python -m failure_analyzer.test_cli --fixture timeout_error --no-ai --verbose
```

### WebSocket Integration

The analyzer is integrated into `MCP_Agent/server.py`. When a failure is detected during test execution, it sends a `failure_analysis` event via WebSocket.

#### WebSocket Event Format

```json
{
  "type": "failure_analysis",
  "data": {
    "analysis_id": "abc12345",
    "failed_step": "Click 'Submit'",
    "failure_category": "ELEMENT_NOT_FOUND",
    "summary": "The test failed because element 'Submit' was not found.",
    "why": "Playwright waited for locator text=Submit until timeout expired.",
    "evidence": [
      "TimeoutError pattern matched",
      "Locator hint: text=Submit",
      "Timeout value: 30000ms"
    ],
    "suggested_fix": "Verify the element exists or update the selector.",
    "confidence": 0.85
  }
}
```

#### Frontend Integration Example

```javascript
// Connect to WebSocket
const ws = new WebSocket(`ws://localhost:8000/ws/sessions/${sessionId}`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'failure_analysis') {
    // Handle failure analysis
    const analysis = data.data;
    console.log(`Failure: ${analysis.failure_category}`);
    console.log(`Summary: ${analysis.summary}`);
    console.log(`Fix: ${analysis.suggested_fix}`);
    
    // Display in UI
    showFailureAnalysis(analysis);
  }
};
```

---

## API Reference

### FailureAnalyzer Class

```python
class FailureAnalyzer:
    def __init__(
        self,
        openai_api_key: Optional[str] = None,  # Defaults to OPENAI_API_KEY env
        openai_model: str = "gpt-4o-mini",
        mock_openai: bool = False
    )
    
    async def analyze(self, raw_event: Dict) -> Dict:
        """Main entry point - returns FailureAnalysis or IgnoredEvent"""
    
    def analyze_sync(self, raw_event: Dict) -> Dict:
        """Synchronous wrapper for analyze()"""
    
    async def analyze_batch(self, events: List[Dict]) -> List[Dict]:
        """Analyze multiple events"""
```

### Output Schema (FailureAnalysis)

| Field | Type | Description |
|-------|------|-------------|
| `analysis_id` | string | Unique ID for this analysis |
| `failed_step` | string? | Step where failure occurred |
| `failure_category` | string | One of the 5 categories |
| `summary` | string | Short human-readable summary |
| `why` | string | Detailed evidence-based explanation |
| `evidence` | string[] | List of detected patterns/facts |
| `suggested_fix` | string | Single actionable suggestion |
| `confidence` | float | 0.0 to 1.0 confidence score |

### Ignored Event Response

```json
{
  "status": "ignored_non_failure_log"
}
```

---

## Configuration

### OpenAI Settings

Modify `openai_client.py`:

```python
# Default model
DEFAULT_MODEL = "gpt-4o-mini"

# In OpenAIAnalysisClient.__init__:
self.max_retries = 3  # Retry attempts on rate limit
```

### Failure Detection Rules

Modify `normalizer.py` to add/remove error indicators:

```python
error_indicators = [
    "error", "timeout", "failed", "exception",
    "assertionerror", "typeerror", "referenceerror",
    "err_connection", "econnrefused", "unexpected",
    "404", "500", "403", "401", "not found", "forbidden"
    # Add more patterns here
]
```

### Classification Rules

Modify `classifier.py` to customize classification:

```python
CLASSIFICATION_RULES = [
    # (regex_pattern, category, evidence_template)
    (r"TimeoutError|Timeout.*exceeded", FailureCategory.ELEMENT_NOT_FOUND, "..."),
    # Add custom rules here
]
```

### AI Prompts

Modify `prompts.py` to customize AI behavior:

```python
SYSTEM_PROMPT = """You are a senior QA automation engineer..."""

def build_analysis_prompt(normalized, classification) -> str:
    # Customize the prompt structure
```

---

## Extending the Module

### Adding a New Failure Category

1. **Add to enum** (`schemas.py`):
```python
class FailureCategory(str, Enum):
    # ... existing categories
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
```

2. **Add classification rule** (`classifier.py`):
```python
CLASSIFICATION_RULES.append((
    r"401|403|unauthorized|forbidden|auth.*fail",
    FailureCategory.AUTHENTICATION_ERROR,
    "Authentication error pattern matched: '{match}'"
))
```

3. **Add description** (`classifier.py`):
```python
# In get_category_description()
FailureCategory.AUTHENTICATION_ERROR: (
    "Authentication or authorization failed..."
),
```

4. **Add fallback response** (`prompts.py`):
```python
# In build_fallback_response()
FailureCategory.AUTHENTICATION_ERROR: {
    "summary": "...",
    "suggested_fix": "..."
}
```

5. **Add test fixture** (`test_fixtures.py`):
```python
"auth_error": {
    "type": "error",
    "payload": {"message": "401 Unauthorized"}
}
```

### Adding New Field Extraction

Modify `normalizer.py`:

```python
# Add new field name variants
NEW_FIELDS = ["newField", "new_field", "newFieldName"]

# In normalize_mcp_event():
new_value = _extract_string(flat, NEW_FIELDS) or None
```

### Custom OpenAI Response Handling

Modify `openai_client.py`:

```python
def _parse_response(self, content, classification):
    data = json.loads(content)
    
    # Add custom post-processing
    if "custom_field" in data:
        # Handle custom response fields
        pass
    
    return result
```

---

## Common Pitfalls

### 1. Missing OpenAI API Key

**Problem**: `openai.AuthenticationError` when running without mock mode

**Solution**:
```bash
export OPENAI_API_KEY=sk-your-key
# Or use mock mode for testing
analyzer = FailureAnalyzer(mock_openai=True)
```

### 2. Event Not Detected as Failure

**Problem**: `is_failure_event()` returns `False` for actual failures

**Solution**: Add the error pattern to `normalizer.py`:
```python
error_indicators = [
    # Add your pattern
    "your_custom_error_text",
]
```

### 3. Wrong Classification

**Problem**: Failure classified as wrong category

**Solution**: Check rule order in `classifier.py` (first match wins):
```python
# Rules are checked in order - put specific patterns first
CLASSIFICATION_RULES = [
    (r"specific_pattern", SPECIFIC_CATEGORY, "..."),
    (r"general_pattern", GENERAL_CATEGORY, "..."),
]
```

### 4. Normalized Data Missing Fields

**Problem**: `normalized.step` is `None` when it should have a value

**Solution**: Add field name variant to `normalizer.py`:
```python
STEP_FIELDS = ["step", "stepName", "step_name", "your_field_name"]
```

### 5. Rate Limiting

**Problem**: OpenAI rate limit errors

**Solution**: The client handles this automatically, but you can adjust:
```python
# In openai_client.py
self.max_retries = 5  # Increase retries
```

### 6. Import Errors

**Problem**: `ModuleNotFoundError: No module named 'failure_analyzer'`

**Solution**: Ensure the Backend directory is in the Python path:
```python
import sys
sys.path.insert(0, "/path/to/Backend")
from failure_analyzer import FailureAnalyzer
```

### 7. Async/Sync Mismatch

**Problem**: `RuntimeError: asyncio.run() cannot be called from a running event loop`

**Solution**: Use the async version in async contexts:
```python
# In async context
result = await analyzer.analyze(event)

# In sync context (scripts)
result = analyzer.analyze_sync(event)
```

### 8. Empty Evidence List

**Problem**: Analysis has empty evidence list

**Solution**: The error message might not match any patterns. Check:
1. Is the message being extracted? (Check `normalizer.py`)
2. Are patterns matching? (Check `classifier.py`)

---

## Testing

### Run All Tests

```bash
cd Backend/failure_analyzer
python -m pytest tests/ -v
```

### Run Specific Test File

```bash
python -m pytest tests/test_classifier.py -v
```

### Run with Coverage

```bash
pip install pytest-cov
python -m pytest tests/ --cov=. --cov-report=html
```

### Test Fixtures

Available fixtures in `test_fixtures.py`:

| Fixture Name | Category | Description |
|--------------|----------|-------------|
| `timeout_error` | ELEMENT_NOT_FOUND | Timeout waiting for locator |
| `element_not_found` | ELEMENT_NOT_FOUND | Element not found |
| `assertion_tobe` | ASSERTION_FAILED | toBe() assertion |
| `assertion_contain` | ASSERTION_FAILED | toContain() assertion |
| `js_typeerror` | JS_ERROR | TypeError |
| `js_referenceerror` | JS_ERROR | ReferenceError |
| `network_connection_refused` | NETWORK_FAILURE | Connection refused |
| `network_http_500` | NETWORK_FAILURE | HTTP 500 |
| `network_http_404` | NETWORK_FAILURE | HTTP 404 |
| `unknown_error` | UNKNOWN | Generic error |
| `missing_fields` | ELEMENT_NOT_FOUND | Minimal event structure |
| `nested_structure` | ELEMENT_NOT_FOUND | Deeply nested JSON |
| `alt_field_names` | ASSERTION_FAILED | Alternative field names |
| `non_failure_info` | (ignored) | Info-level log |
| `non_failure_success` | (ignored) | Success status |

---

## Troubleshooting

### Debug Logging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("failure_analyzer").setLevel(logging.DEBUG)
```

### Inspect Normalization

```python
from failure_analyzer import normalize_mcp_event

normalized = normalize_mcp_event(raw_event)
print(f"Raw message: {normalized.raw_message}")
print(f"Step: {normalized.step}")
print(f"Locator hints: {normalized.locator_hints}")
print(f"Console: {normalized.console_lines}")
print(f"Network: {normalized.network_lines}")
```

### Inspect Classification

```python
from failure_analyzer import classify_failure, normalize_mcp_event

normalized = normalize_mcp_event(raw_event)
classification = classify_failure(normalized)

print(f"Category: {classification.category}")
print(f"Evidence: {classification.evidence}")
print(f"Confidence modifier: {classification.confidence_modifier}")
```

### Check WebSocket Events

In `MCP_Agent/server.py`, the analyzer logs to console:

```
Failure analyzed: ELEMENT_NOT_FOUND - The test failed because...
```

---

## Integration Checklist

When integrating with a new component:

- [ ] Install dependencies (`openai`, `pydantic`)
- [ ] Set `OPENAI_API_KEY` environment variable
- [ ] Import from `failure_analyzer` package
- [ ] Create `FailureAnalyzer` instance (consider mock mode for dev)
- [ ] Use `is_failure_event()` to filter events
- [ ] Call `await analyzer.analyze()` on failure events
- [ ] Handle `ignored_non_failure_log` status in responses
- [ ] Display `failure_category`, `summary`, and `suggested_fix` to users
- [ ] Run tests: `python -m pytest tests/ -v`

---

## Support

For issues or questions:
1. Check [Common Pitfalls](#common-pitfalls)
2. Enable [Debug Logging](#debug-logging)
3. Run the [CLI Testing Tool](#cli-testing-tool) to isolate issues
4. Check test fixtures for expected input/output formats
