# JSON Parsing Enhancements

This document describes enhancements made to the JSON parsing capabilities of the Zendesk AI Integration.

## Overview

When using AI services like OpenAI's GPT models or Anthropic's Claude, responses may be returned in different formats:

1. Direct JSON objects
2. JSON wrapped in markdown code blocks
3. Text with embedded JSON code blocks

The application has been enhanced to handle all these cases robustly.

## Implemented Fixes

### 1. JSON Extraction from Code Blocks

Both `ai_service.py` and `claude_service.py` have been updated to extract JSON from markdown code blocks:

```python
# Try to parse as JSON
try:
    # First try direct JSON parsing
    return json.loads(content)
except json.JSONDecodeError:
    # Check if JSON is wrapped in a code block
    if '```json' in content and '```' in content.split('```json', 1)[1]:
        # Extract content between ```json and the next ```
        json_content = content.split('```json', 1)[1].split('```', 1)[0].strip()
        try:
            return json.loads(json_content)
        except json.JSONDecodeError:
            # If still not valid JSON, return as raw text
            return {"raw_text": content}
    else:
        # If not valid JSON and not in code block, return as raw text
        return {"raw_text": content}
```

### 2. Confidence Value Handling

Both services now handle text-based confidence values, mapping them to appropriate numeric values:

```python
# Handle confidence - convert text values to numeric
confidence_value = result.get("confidence", 0.9)
if isinstance(confidence_value, str):
    # Map text confidence levels to numeric values
    confidence_map = {
        "high": 0.9,
        "medium": 0.7,
        "low": 0.5,
        "veryhigh": 1.0,
        "verylow": 0.3
    }
    # Convert to lowercase and remove spaces for matching
    confidence_key = confidence_value.lower().replace(" ", "")
    confidence = confidence_map.get(confidence_key, 0.9)
else:
    # Try to convert to float, default to 0.9 if fails
    try:
        confidence = float(confidence_value)
    except (ValueError, TypeError):
        confidence = 0.9
```

### 3. Component Handling in Claude Service

The Claude service can sometimes return components as lists instead of strings. This is now handled properly:

```python
# Handle component which might be a list or string
component_value = result.get("component", "none")
if isinstance(component_value, list) and len(component_value) > 0:
    component = str(component_value[0]).lower().replace(" ", "_")
elif isinstance(component_value, str):
    component = component_value.lower().replace(" ", "_")
else:
    component = "none"
```

## Testing

Tests have been updated to ensure proper loading of environment variables from `.env` files:

```python
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()
```

These enhancements ensure consistent behavior regardless of the AI service being used (OpenAI or Claude) and the format of the response.
