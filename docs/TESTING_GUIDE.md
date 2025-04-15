# Testing Guide for Zendesk AI Integration

This guide explains how to properly write and run tests for the Zendesk AI Integration project, with special focus on mocking external APIs like OpenAI.

## Testing Architecture

Our testing architecture is divided into different types of tests:

1. **Unit Tests**: Test individual functions in isolation with explicit mocks
2. **Integration Tests**: Test interactions between components with comprehensive mocking
3. **Functional Tests**: Test end-to-end flows
4. **Performance Tests**: Test system performance under various conditions

## Mocking External APIs

### How Our Mocking System Works

We use a multi-layered approach to ensure all external API calls are properly mocked:

1. **Monkey Patching**: Direct replacement of API functions at module load time
2. **Pytest Fixtures**: Automatic fixtures that apply mocks based on test type
3. **Explicit Test Mocks**: Test-specific mocks for fine-grained control

### Mocking OpenAI API

To properly mock OpenAI API calls in your tests:

#### For Unit Tests

Use explicit mocking within each test:

```python
from unittest.mock import patch

def test_something():
    with patch('src.ai_service.get_completion_from_openai') as mock_get_completion:
        mock_get_completion.return_value = '{"sentiment": {"polarity": "positive"}}'
        # Your test code
```

#### For Integration Tests

For integration tests, the mocking is done automatically by importing our mock module:

```python
# This will apply the patches automatically - add this to your Python test file
import tests.integration.openai_mock

def test_integration_feature():
    # API calls will be automatically mocked
    result = my_function_that_uses_openai()
    assert result["sentiment"]["polarity"] == "positive"
```

**IMPORTANT**: The import statement should be inside your Python test files, not run directly in the command line or PowerShell.

Alternatively, you can rely on the automatic fixture in `tests/integration/conftest.py` which is applied to all integration tests.

## Running Tests

### Running Unit Tests

```bash
pytest tests/unit/ -v
```

### Running Integration Tests

```bash
pytest tests/integration/ -v
```

### Using the Test Runner Script

For the most reliable test setup, use our custom test runner script:

```bash
python run_tests.py tests/integration/test_sentiment_analysis_mock.py -v
```

This script automatically:
- Sets up the correct test environment variables
- Ensures proper Python path configuration
- Applies the mocking system consistently

### Running Specific Tests

```bash
# Run a specific test file
pytest tests/unit/test_ai_service.py -v

# Run a specific test function
pytest tests/integration/test_sentiment_analysis_mock.py::test_sentiment_analysis_structure -v

# Run tests matching a pattern
pytest -k "sentiment"
```

### Controlling Test Verbosity

```bash
# Show log output
pytest tests/integration/test_sentiment_analysis_mock.py -v --log-cli-level=INFO
```

## Troubleshooting Tests

### Common Issues

1. **API Calls Are Still Being Made**: If you see real API calls being attempted:
   - Make sure you're importing the mock module correctly
   - Check that the path in the `patch()` call matches the actual import path
   - Use `patch.object()` for more direct mocking

2. **Tests Pass Locally But Fail in CI**: This might be due to:
   - Environment variable differences
   - Different Python versions
   - Timing issues

3. **Mock Not Being Applied**: This can happen if:
   - The mock is applied after the module is imported
   - The import path is incorrect
   - The module is imported in a way that bypasses the mock

4. **Function Named as Test**: Any functions in test files starting with `test_` will be treated as test functions by pytest. If you're creating helper functions, prefix them with `_` instead.

### Debugging Techniques

1. Add `--log-cli-level=DEBUG` to see detailed logs
2. Use `print()` statements in your test to verify mock behavior
3. Check if the mock is being applied by adding a distinctive log message

## Writing New Tests

When writing new tests that interact with external APIs:

1. **Always mock external dependencies**
2. **Use explicit mocks for unit tests**
3. **Use our mock system for integration tests**
4. **Test both success and error cases**
5. **Prefix helper functions with `_` to avoid them being treated as tests**

## Mock Response Structure

When creating mock responses for OpenAI API calls, follow this structure:

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
