# Zendesk AI Integration Architecture

This document outlines the architecture of the Zendesk AI Integration application based on the fully implemented Clean Architecture approach.

## Architecture Overview

The application is structured using Clean Architecture principles with the following layers:

1. **Domain Layer** - Core business logic and domain models without external dependencies
2. **Application Layer** - Orchestrates the business logic and use cases
3. **Infrastructure Layer** - Implements interfaces and handles external dependencies
4. **Presentation Layer** - Provides user interfaces and API endpoints

### Layer Dependencies

Dependencies follow the Clean Architecture dependency rule and only point inward:
- Presentation Layer → Application Layer → Domain Layer
- Infrastructure Layer → Domain Layer

The domain layer has no dependencies on other layers, ensuring that business logic remains independent of technical implementations.

## Layer Details

### Domain Layer (`src/domain`)

The domain layer contains the core business logic and domain models:

- **Entities** (`domain/entities/`)
  - `ticket.py` - Core ticket entity with business logic
  - `ticket_analysis.py` - Analysis results as a domain entity

- **Value Objects** (`domain/value_objects/`)
  - `sentiment_polarity.py` - Sentiment classification values
  - `ticket_category.py` - Ticket category classifications
  - `ticket_priority.py` - Priority levels for tickets
  - `ticket_status.py` - Possible ticket statuses
  - `hardware_component.py` - Hardware component types

- **Interfaces** (`domain/interfaces/`)
  - `ai_service_interfaces.py` - Abstractions for AI services
  - `repository_interfaces.py` - Data access abstractions
  - `service_interfaces.py` - Domain service abstractions
  - `cache_interfaces.py` - Caching mechanism abstractions
  - `reporter_interfaces.py` - Reporting functionality abstractions
  - `utility_interfaces.py` - Utility functionality abstractions

- **Exceptions** (`domain/exceptions.py`)
  - Domain-specific exception types for better error handling

### Application Layer (`src/application`)

The application layer orchestrates the business use cases:

- **Use Cases** (`application/use_cases/`)
  - `analyze_ticket_use_case.py` - Coordinates ticket analysis workflow
  - `generate_report_use_case.py` - Coordinates report generation

- **Services** (`application/services/`)
  - `ticket_analysis_service.py` - Implements analysis workflow logic
  - `reporting_service.py` - Implements report generation logic
  - `webhook_service.py` - Handles webhook processing logic
  - `scheduler_service.py` - Manages scheduled operations

- **DTOs** (`application/dtos/`)
  - `ticket_dto.py` - Data transfer object for tickets
  - `analysis_dto.py` - Data transfer object for analysis results
  - `report_dto.py` - Data transfer object for reports

### Infrastructure Layer (`src/infrastructure`)

The infrastructure layer provides concrete implementations:

- **Repositories** (`infrastructure/repositories/`)
  - `mongodb_repository.py` - MongoDB implementation of repositories
  - `zendesk_repository.py` - Zendesk API implementation

- **External Services** (`infrastructure/external_services/`)
  - `claude_service.py` - Claude AI service implementation
  - `openai_service.py` - OpenAI service implementation

- **Cache** (`infrastructure/cache/`)
  - `zendesk_cache_adapter.py` - Caching implementation for Zendesk data

- **Utils** (`infrastructure/utils/`)
  - `config_manager.py` - Configuration management
  - `dependency_injection.py` - Dependency injection container
  - `retry.py` - Retry mechanisms for external calls
  - `service_provider.py` - Service locator for dependencies

### Presentation Layer (`src/presentation`)

The presentation layer provides user interfaces:

- **CLI** (`presentation/cli/`)
  - `command.py` - Base command interface
  - `command_handler.py` - Command registration and execution
  - `commands/` - Individual command implementations
  - `response_formatter.py` - Formats command responses

- **Webhook** (`presentation/webhook/`)
  - `webhook_handler.py` - Webhook request processing

- **Reporters** (`presentation/reporters/`)
  - `hardware_reporter.py` - Hardware component reporting
  - `sentiment_reporter.py` - Sentiment analysis reporting
  - `pending_reporter.py` - Pending tickets reporting

## Component Interactions

### Ticket Analysis Flow

1. User initiates an analysis through the command-line interface
2. `CommandHandler` identifies and executes the appropriate command
3. Command uses the `AnalyzeTicketUseCase`
4. Use case coordinates between repositories and services
5. AI Service performs the actual analysis
6. Results are saved through the repository
7. Response is formatted and returned to the user

### Reporting Flow

1. User requests a report through the command-line interface
2. `CommandHandler` executes the appropriate report command
3. Command uses the `GenerateReportUseCase`
4. Use case retrieves data through repositories
5. Data is processed and formatted into a report
6. Report is returned to the user or saved to a file

### Webhook Flow

1. External system sends a webhook request
2. `WebhookHandler` processes the request
3. Handler validates the request and extracts ticket information
4. `WebhookService` processes the ticket using the appropriate use case
5. Response is sent back to the external system

## Dependency Injection

The application uses a custom dependency injection container to manage dependencies:

```python
# Register dependencies
container.register_class(TicketRepository, ZendeskTicketRepository)
container.register_class(AIService, ClaudeService)  # or OpenAIService
container.register_instance(ConfigManager, config_manager)

# Resolve dependencies
ticket_repository = container.resolve(TicketRepository)
ai_service = container.resolve(AIService)
```

This approach ensures loose coupling between components and improves testability.

## AI Service Implementation

The application provides a consistent interface for different AI providers:

- **Provider Abstraction**: Common interface for OpenAI and Claude
- **Error Handling**: Consistent error handling across providers
- **Retry Logic**: Exponential backoff with jitter for API calls
- **Rate Limiting**: Intelligent handling of rate limits

## Caching Strategy

The application implements a multi-level caching strategy:

- **Request Caching**: Caches Zendesk API responses to reduce API calls
- **Analysis Caching**: Caches analysis results to avoid redundant processing
- **TTL Management**: Time-based cache invalidation
- **Smart Invalidation**: Event-based cache invalidation for data consistency

## Error Handling

The application implements a comprehensive error handling strategy:

- **Domain-Specific Exceptions**: Custom exception types for different error scenarios
- **Retry Mechanisms**: Automatic retries for transient failures
- **Graceful Degradation**: Fallback behaviors when services are unavailable
- **Structured Logging**: Detailed error logging for troubleshooting

## Testing Strategy

The application is tested at multiple levels:

- **Unit Tests** (`tests/unit/`): Test individual components in isolation
- **Integration Tests** (`tests/integration/`): Test interactions between components
- **Functional Tests** (`tests/functional/`): Test end-to-end functionality
- **Performance Tests** (`tests/performance/`): Test performance characteristics

Tests use mocks and stubs to isolate the system under test from external dependencies.

## Configuration Management

Configuration is managed through environment variables with sensible defaults:

```python
# Environment-based configuration with prefix
config = EnvironmentConfigManager(prefix="ZENDESK_AI_")

# Get configuration values with defaults
api_key = config.get("api_key", default=None)
timeout = config.get_int("timeout", default=30)
retries = config.get_int("retries", default=3)
```

## Current Status

The clean architecture implementation is complete across all layers:

1. **Domain Layer**: ✅ Fully implemented with interfaces, entities, and value objects
2. **Application Layer**: ✅ Fully implemented with use cases and services
3. **Infrastructure Layer**: ✅ Fully implemented with repository and service adapters
4. **Presentation Layer**: ✅ Fully implemented with command pattern and response formatting

The transition from the legacy architecture to clean architecture is now complete, with all compatibility layers removed and all components following the clean architecture principles.

## Future Enhancements

Potential architectural enhancements for future iterations:

1. **Event-Driven Architecture**: Implement domain events for better decoupling
2. **CQRS Pattern**: Separate command and query responsibilities
3. **Microservices**: Split functionality into separate services
4. **API Gateway**: Add an API gateway for better API management
