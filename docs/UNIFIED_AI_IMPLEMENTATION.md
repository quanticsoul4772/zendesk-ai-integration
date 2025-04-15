# Unified AI Implementation

This document details the consolidated AI implementation for the Zendesk AI Integration project, which provides a unified interface for working with multiple AI providers (OpenAI and Claude).

## Overview

The unified AI architecture consists of three key components:

1. **UnifiedAIService** - A centralized service class that provides a consistent interface to different AI providers
2. **Unified Sentiment Analysis** - A streamlined approach to sentiment analysis that works across providers
3. **Updated AIAnalyzer** - Enhanced analyzer module that leverages the unified services

This consolidation eliminates code duplication, provides consistent error handling, and makes it easy to switch between providers or add new ones.

## Components

### UnifiedAIService

The `UnifiedAIService` class provides a common interface for interacting with different AI providers:

```python
from src.unified_ai_service import UnifiedAIService

# Initialize with Claude (default)
claude_service = UnifiedAIService()

# Initialize with OpenAI
openai_service = UnifiedAIService(provider="openai")

# Get completion
result = claude_service.get_completion(
    prompt="Analyze this support ticket...",
    model="claude-3-haiku-20240307",  # Optional, uses defaults if not specified
    temperature=0.3
)

# Analyze sentiment directly
analysis = claude_service.analyze_sentiment(
    content="My system keeps crashing when I try to run my application.",
    use_enhanced=True  # Use enhanced sentiment analysis
)
```

#### Key Features

- **Provider abstraction**: Hides the differences between OpenAI and Claude APIs
- **Consistent error handling**: Common error types and retry mechanisms
- **Automatic backoff**: Implements exponential backoff with jitter for rate limits
- **JSON parsing**: Automatically extracts and parses JSON from responses
- **Direct sentiment analysis**: Includes built-in sentiment analysis functionality

### Unified Sentiment Analysis

The `unified_sentiment` module provides a simplified interface for sentiment analysis:

```python
from src.unified_sentiment import analyze_sentiment

# Analyze with Claude (default)
claude_analysis = analyze_sentiment(
    content="My system is experiencing intermittent crashes.",
    use_enhanced=True,  # Use enhanced sentiment analysis
    ai_provider="claude"
)

# Analyze with OpenAI
openai_analysis = analyze_sentiment(
    content="My system is experiencing intermittent crashes.",
    use_enhanced=True,
    ai_provider="openai"
)
```

#### Key Features

- **Simplified interface**: One function that works with any provider
- **Multiple fallback mechanisms**: Falls back gracefully if services are unavailable
- **Consistent response format**: Normalized output regardless of provider
- **Automatic priority scoring**: Calculates priority score based on sentiment metrics

### Updated AIAnalyzer

The `AIAnalyzer` class has been updated to fully leverage the unified services:

```python
from modules.ai_analyzer import AIAnalyzer

analyzer = AIAnalyzer()

# Analyze a single ticket
analysis = analyzer.analyze_ticket(
    ticket_id="123",
    subject="System crash on startup",
    description="My system keeps crashing when starting up...",
    use_enhanced=True,
    use_claude=True  # Use Claude (False for OpenAI)
)

# Analyze a batch of tickets
results = analyzer.analyze_tickets_batch(
    tickets=tickets_list,
    use_enhanced=True,
    use_claude=True
)
```

#### Key Features

- **Lazy initialization**: Services are initialized on-demand
- **Multiple fallbacks**: Falls back to different implementations if needed
- **Optimized batch processing**: Efficiently processes multiple tickets in parallel
- **Consistent formatting**: Clean presentation of analysis results

## Implementation Details

### Error Handling

The unified implementation includes comprehensive error handling:

- **Rate limiting**: Automatically handles rate limits with exponential backoff
- **Token limits**: Detects and reports token limit issues
- **Content filtering**: Handles content policy violations
- **Network errors**: Manages timeouts and connection issues
- **Dependency errors**: Gracefully handles missing dependencies

### Response Formatting

Sentiment analysis results are consistently formatted regardless of provider:

```json
{
  "sentiment": {
    "polarity": "negative",
    "urgency_level": 4,
    "frustration_level": 3,
    "technical_expertise": 2,
    "business_impact": {
      "detected": true,
      "description": "Production system down affecting operations"
    },
    "key_phrases": ["system down", "urgent fix", "production impact"],
    "emotions": ["frustration", "urgency"]
  },
  "category": "hardware_issue",
  "component": "gpu",
  "priority_score": 8,
  "confidence": 0.95
}
```

### Priority Scoring

Priority scores are calculated using a weighted algorithm based on:

- Urgency level (35% weight)
- Frustration level (30% weight)
- Business impact (25% weight)
- Technical expertise (10% weight, inverse relationship)

The final score is on a scale of 1-10, where 10 represents the highest priority.

## Integration

### Importing Services

```python
# Import unified services
from src.unified_ai_service import UnifiedAIService
from src.unified_sentiment import analyze_sentiment

# Import AI analyzer
from modules.ai_analyzer import AIAnalyzer
```

### Configuration

No special configuration is needed. The services will use environment variables for API keys:

- `OPENAI_API_KEY` - For OpenAI services
- `ANTHROPIC_API_KEY` - For Claude services

API keys can also be provided directly to the service:

```python
service = UnifiedAIService(provider="openai", api_key="your-api-key")
```

## Best Practices

1. **Use the highest level of abstraction** for your needs:
   - For simple sentiment analysis, use `analyze_sentiment` from `unified_sentiment`
   - For more control or custom prompts, use `UnifiedAIService` directly
   - For batch ticket processing, use `AIAnalyzer.analyze_tickets_batch`

2. **Handle errors appropriately**:
   - Check for `error` keys in response dictionaries
   - Use try/except blocks for critical functions

3. **Optimize concurrency**:
   - Adjust `max_concurrency` in batch operations based on your rate limits
   - Use the batch processor for parallel processing

4. **Switch providers seamlessly**:
   - Simply change the `provider` parameter to use a different AI service
   - Or set `use_claude=False` in the analyzer to use OpenAI

## Testing

The unified implementation includes comprehensive tests:

```bash
# Run the unified service tests
pytest tests/test_unified_service.py -v
```

The tests cover initialization, completion processing, sentiment analysis, error handling, and fallback mechanisms.
