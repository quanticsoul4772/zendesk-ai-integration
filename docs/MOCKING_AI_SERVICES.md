# Mocking AI Services in Tests

This document describes how to properly mock OpenAI and other AI service calls in your tests to ensure:

1. Tests are deterministic and reliable
2. Tests run without requiring valid API keys
3. Tests execute quickly without external API dependencies
4. Test results are consistent across environments

## Integration Test Mocking

Integration tests should use the automatic mocking provided by the `conftest.py` file in the `tests/integration` directory. This file includes an `autouse=True` fixture that automatically mocks all OpenAI API calls.

### How the Mock Works

The mock intercepts calls to:
- `src.ai_service.call_openai_with_retries`
- `src.ai_service.get_completion_from_openai`

It analyzes the content of the prompt and returns appropriate predefined responses for different scenarios (low, medium, high urgency, etc.).

### Example Usage

```python
# Your integration test
def test_my_feature():
    # You don't need to do anything special
    # OpenAI calls are automatically mocked
    result = my_function_that_uses_openai()
    assert result["sentiment"]["polarity"] == "positive"
```

## Unit Test Mocking

For unit tests, you should explicitly mock the OpenAI calls using the `unittest.mock` module:

```python
from unittest.mock import patch

def test_something():
    with patch('src.ai_service.get_completion_from_openai') as mock_get_completion:
        # Configure the mock to return a specific JSON response
        mock_get_completion.return_value = '''
        {
            "sentiment": {
                "polarity": "negative",
                "urgency_level": 4
            }
        }
        '''
        
        # Your test code here
        result = my_function()
        assert result["sentiment"]["polarity"] == "negative"
```

## Mock Response Structure

When creating mock responses, follow this structure:

```python
{
    "sentiment": {
        "polarity": "positive|negative|neutral",
        "urgency_level": 1-5,
        "frustration_level": 1-5,
        "technical_expertise": 1-5,
        "business_impact": {
            "detected": True|False,
            "description": "Description if detected"
        },
        "key_phrases": ["phrase1", "phrase2"],
        "emotions": ["emotion1", "emotion2"]
    },
    "category": "category_name",
    "component": "component_name",
    "confidence": 0.0-1.0
}
```

## Adding New Mock Responses

To add new mock responses for different test scenarios:

1. Open `tests/integration/conftest.py`
2. Add your new response to the `responses` dictionary
3. Update the `mock_call_openai` function to detect and return your new response

## Debugging Mock Issues

If your tests are still attempting to call the real OpenAI API:

1. Check for direct imports of OpenAI client in your code
2. Make sure the correct paths are being patched
3. Verify that the `conftest.py` file is being loaded (it should be automatic for the directory it's in)
4. Add debug logging to confirm which functions are being called

## Best Practices

1. Never hardcode API keys in tests or test fixtures
2. Always use mocking for external API calls
3. Keep mock responses as close to real responses as possible
4. Consider using a parameter in functions to inject mocks for testing
5. For complex scenarios, consider creating more specialized mock responses
