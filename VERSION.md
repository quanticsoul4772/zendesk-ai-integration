# Version History

## v1.5.0 (March 30, 2025)

### Major Updates
- Added support for OpenAI's GPT-4o model
- Updated to Claude 3 models (Haiku, Sonnet) as primary models
- Enhanced error handling and resilience for API changes
- Improved JSON parsing for more reliable structured outputs

### Dependency Updates
- Updated dependencies to latest versions:
  - zenpy 2.0.56
  - openai 1.63.0
  - anthropic 0.49.0
  - pymongo 4.11.3
  - motor 3.7.0
  - flask 3.1.0
  - requests 2.32.3
  - python-dotenv 1.0.0
  - pytest 8.3.0

### Configuration Changes
- Added more configuration options in .env file
- Enhanced cache configuration settings
- Added performance tuning parameters

### Documentation
- Updated README with latest model information
- Improved installation and configuration instructions
- Updated SENTIMENT_ANALYSIS.md with latest models and features
- Added VERSION.md to track version history

## v1.4.0 (September 2024)

### Major Updates
- Added multi-view analysis support
- Enhanced reporting with descriptive labels
- Improved hardware component detection
- Added parallel batch processing for ticket analysis

### Configuration Changes
- Added MongoDB connection options
- Added view caching controls

### Bug Fixes
- Fixed issue with cached Zendesk views becoming stale
- Fixed MongoDB connection timeout issues
- Fixed unicode handling in reports

## v1.3.0 (May 2024)

### Major Updates
- Added Claude integration for sentiment analysis
- Enhanced sentiment analysis with business impact detection
- Implemented caching system for Zendesk data

### Bug Fixes
- Fixed webhook signature verification
- Fixed report generation for large ticket volumes

## v1.2.0 (January 2024)

### Major Updates
- Added webhook integration
- Implemented scheduled analysis
- Added MongoDB support for analytics
- Enhanced security features

## v1.1.0 (October 2023)

### Major Updates
- Enhanced sentiment analysis with urgency detection
- Added reporting capabilities
- Improved error handling

## v1.0.0 (July 2023)

### Initial Release
- Basic sentiment analysis using OpenAI GPT-3.5
- Zendesk API integration
- Command-line interface
