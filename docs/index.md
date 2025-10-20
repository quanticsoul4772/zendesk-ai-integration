# Zendesk AI Integration Documentation

Welcome to the Zendesk AI Integration documentation. This project provides AI-powered ticket analysis and reporting capabilities for Zendesk support systems.

## Overview

The Zendesk AI Integration leverages advanced AI services (OpenAI and Anthropic Claude) to analyze support tickets, extract insights, and generate comprehensive reports. Built with Clean Architecture principles, the system is modular, testable, and maintainable.

## Key Features

- **AI-Powered Ticket Analysis**: Analyze tickets using OpenAI or Claude AI for sentiment, categorization, and priority assessment
- **Multi-View Reporting**: Generate reports across different Zendesk views with intelligent caching
- **Sentiment Analysis**: Advanced sentiment analysis with polarity scores and emotional context
- **Performance Optimization**: Batch processing, caching, and optimized database queries
- **Clean Architecture**: Separation of concerns with clear boundaries between layers
- **Comprehensive Testing**: Unit, integration, functional, and performance tests

## Quick Start

For installation instructions, see [Installation Guide](../INSTALLATION.md).

For usage examples, see [README](../README.md).

## Architecture

The application follows Clean Architecture principles with four main layers:

- **Domain Layer**: Core business logic and entities
- **Application Layer**: Use cases and application services
- **Infrastructure Layer**: External services, repositories, and utilities
- **Presentation Layer**: CLI, reporters, and webhook handlers

For detailed architecture documentation, see the [Architecture Guide](ARCHITECTURE.md).

## Documentation Sections

### Getting Started
- [Installation](../INSTALLATION.md)
- [Usage Guide](../README.md)
- [Command Reference](../COMMAND_REFERENCE.md)

### Features
- [Sentiment Analysis](../SENTIMENT_ANALYSIS.md)
- [Multi-View Reporting](../MULTI_VIEW_REPORTING.md)
- [Enhanced Reports](../ENHANCED_REPORTS.md)
- [Performance Optimization](../PERFORMANCE_OPTIMIZATION.md)

### Development
- [Testing Guide](../TESTING.md)
- [Contributing](../CONTRIBUTING.md)
- [Code Coverage](../CODE_COVERAGE.md)

### Setup & Configuration
- [MongoDB Setup](../MONGODB_SETUP.md)
- [Webhook Setup](../WEBHOOK_SETUP.md)
- [Pre-commit Hooks](../PRE_COMMIT_SETUP.md)

## Support

For questions, issues, or contributions, please refer to our [Contributing Guide](../CONTRIBUTING.md).

## License

This project is licensed under the terms specified in the repository.
