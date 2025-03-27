# Sentiment Analysis Methodology

> **Note**: Enhanced sentiment analysis is now the standard for all operations in this application. This document describes the comprehensive sentiment analysis methodology used throughout the system.

This document explains the sentiment analysis approach used in our Zendesk AI Integration application.

## Overview

Our application employs advanced sentiment analysis to extract nuanced emotional and business insights from customer support tickets. The system leverages large language models (LLMs) from both OpenAI and Anthropic to analyze customer language patterns, detect emotional signals, and assess business impact.

## Models Used

The application supports two AI providers:

1. **OpenAI**
   - Primary model: GPT-4o
   - Fallback model: GPT-3.5 Turbo

2. **Anthropic Claude**
   - Primary model: Claude-3-Haiku-20240307
   - Fallback models: Claude-3-Sonnet, Claude-3-Haiku, Claude-2.1, Claude-Instant-1.2

## Sentiment Analysis Components

Our enhanced sentiment analysis extracts the following information from each support ticket:

### 1. Sentiment Polarity

Basic sentiment classification:
- **Positive**: Customer expresses satisfaction or positive emotions
- **Negative**: Customer expresses dissatisfaction or negative emotions
- **Neutral**: Customer communication is factual or balanced
- **Unknown**: Sentiment cannot be reliably determined

### 2. Urgency Level (1-5 Scale)

Indicates how time-sensitive the customer's issue is:

- **Level 1**: Non-urgent, general inquiries
  - Example: "Just checking in about my order status"
- **Level 2**: Minor issues without significant impact
  - Example: "My system is having minor issues that aren't affecting work"
- **Level 3**: Moderate issues affecting productivity
  - Example: "System is having intermittent issues impacting productivity"
- **Level 4**: Serious issues requiring prompt resolution
  - Example: "System is down and we need it fixed very soon"
- **Level 5**: Critical emergency with major business impact
  - Example: "CRITICAL: Production system completely down, losing $10k/hour"

### 3. Frustration Level (1-5 Scale)

Measures customer's emotional state:

- **Level 1**: Satisfied, positive tone
  - Example: "Thanks for your assistance with my question"
- **Level 2**: Neutral or mildly concerned
  - Example: "I'd appreciate help resolving this issue"
- **Level 3**: Noticeable frustration
  - Example: "I've been waiting for several days to get this resolved"
- **Level 4**: High frustration
  - Example: "This is quite frustrating as I've reported this twice now"
- **Level 5**: Extreme frustration
  - Example: "This is now the THIRD time I've had to contact support about this same ISSUE!"

### 4. Technical Expertise Assessment (1-5 Scale)

Evaluates the customer's technical knowledge level:

- **Level 1**: Basic user
  - Example: "I'm not sure what a driver is"
- **Level 2**: Beginner
  - Example: "I know how to install software but not hardware"
- **Level 3**: Intermediate
  - Example: "I've updated drivers and checked system logs"
- **Level 4**: Advanced
  - Example: "I've tried replacing components and running diagnostics"
- **Level 5**: Expert
  - Example: "I've already analyzed the memory dumps and identified a potential IRQ conflict"

### 5. Business Impact Detection

Identifies whether the issue is affecting business operations:

- **Detected**: Boolean flag (true/false)
- **Description**: Text description of the specific business impact

Common business impact patterns:
- Production system downtime
- Revenue loss
- Missed deadlines
- Customer-facing issues
- Contractual obligations at risk

### 6. Additional Metadata

- **Key phrases**: Notable phrases showing sentiment (up to 3)
- **Emotions**: Array of detected emotions (anger, worry, satisfaction, etc.)
- **Confidence**: AI confidence score for the analysis (0.0-1.0)

## Priority Score Calculation

The system calculates a priority score (1-10) based on multiple factors:

```
Priority Score = (Urgency × 0.35) + (Frustration × 0.3) + (Business Impact × 0.25) + (Technical Expertise Adjusted × 0.1)
```

Where:
- **Urgency**: 1-5 scale
- **Frustration**: 1-5 scale
- **Business Impact**: 0 or 5 (0 if not detected, 5 if detected)
- **Technical Expertise Adjusted**: Inverted scale (5 = 1, 4 = 2, 3 = 3, 2 = 4, 1 = 5)

The technical expertise is inverted because less technical customers may need more assistance, resulting in higher priority.

## Implementation Details

### Enhanced Prompt Design

The system uses carefully crafted prompts with examples for each category to improve classification accuracy. The prompts include:

1. Clear instructions for AI analysis
2. Domain-specific context (hardware support for Exxact Corporation)
3. Calibration examples for each level
4. Instructions to focus on business impact signals
5. Guidance for detecting frustration signals (repeated contact attempts, strong language, excessive punctuation)

### Error Handling

The system implements robust error handling:
- Exponential backoff with jitter for rate limiting
- Fallback to alternative models when primary models are unavailable
- Default sentiment values for error cases
- Detailed logging for troubleshooting

### Model Configuration

- **Temperature**: 0.3 (low to ensure consistency)
- **Max Tokens**: 4096 (sufficient for comprehensive analysis)
- **System Prompt**: Ensures consistent JSON formatting

## Best Practices

This implementation follows industry best practices for sentiment analysis in customer support:

1. **Multi-dimensional analysis**: Goes beyond basic polarity to include urgency, frustration, and business impact
2. **Contextual evaluation**: Uses domain-specific examples for better accuracy
3. **Priority scoring**: Combines multiple factors for holistic assessment
4. **Confidence scoring**: Provides transparency about analysis reliability
5. **Business impact focus**: Prioritizes issues with potential revenue impact

## Usage in Reports

The sentiment analysis data powers various reports:
- Sentiment distribution analysis
- Urgency and frustration level reporting
- Business impact assessment
- High-priority ticket identification
- Trend analysis over time

For more information on reporting, see [REPORTING.md](REPORTING.md).
