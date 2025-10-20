# Zendesk AI Integration Architecture

This document outlines the architecture of the Zendesk AI Integration application based on the refactored design following clean architecture principles.

## Architecture Overview

The application is structured using a Clean Architecture approach with the following layers:

1. **Domain Layer** - Contains the business logic and domain models
2. **Application Layer** - Orchestrates the business logic
3. **Infrastructure Layer** - Handles external dependencies
4. **Presentation Layer** - Provides various interfaces (CLI, API, etc.)

### Layer Dependencies

Dependencies only point inward:
- Presentation Layer → Application Layer → Domain Layer
- Infrastructure Layer → Domain Layer

The domain layer has no dependencies on other layers.

## Key Components

### Domain Layer (`src/domain`)

Contains the core business logic and domain models:

- **Entities** - Business objects with identity and lifecycle
- **Value Objects** - Immutable objects with no identity
- **Interfaces** - Abstract definitions for services and repositories
- **Domain Services** - Business logic that operates on multiple entities
- **Exceptions** - Domain-specific exceptions

### Application Layer (`src/application`)

Orchestrates the business use cases:

- **Service Implementations** - Implementations of domain service interfaces
- **Use Cases** - Orchestration of domain entities and services
- **DTOs** - Data transfer objects for communication between layers

### Infrastructure Layer (`src/infrastructure`)

Provides implementations for external dependencies:

- **Repositories** - Implementations of repository interfaces
- **External Services** - Integration with external systems (Zendesk, AI services)
- **Database** - Database access
- **Caching** - Caching mechanisms
- **Utils** - Common infrastructure utilities

### Presentation Layer (`src/presentation`)

Provides user interfaces:

- **CLI** - Command-line interface
- **API** - RESTful API
- **Webhook** - Webhook handlers
- **Menu** - Interactive menu system

## Module Structure

```
src/
├── domain/
│   ├── entities/
│   ├── interfaces/
│   ├── value_objects/
│   ├── exceptions.py
│   └── __init__.py
├── application/
│   ├── services/
│   ├── use_cases/
│   ├── dtos/
│   └── __init__.py
├── infrastructure/
│   ├── repositories/
│   ├── external_services/
│   ├── database/
│   ├── cache/
│   ├── utils/
│   └── __init__.py
├── presentation/
│   ├── cli/
│   ├── api/
│   ├── webhook/
│   ├── menu/
│   └── __init__.py
└── __init__.py
```

## Dependency Injection

The application uses a simple dependency injection container to manage dependencies between components. This allows for better testability and loose coupling between implementations.

Example usage:

```python
# Register dependencies
container.register_class(TicketRepository, ZendeskTicketRepository)
container.register_class(AIService, OpenAIService)

# Resolve dependencies
ticket_repository = container.resolve(TicketRepository)
ai_service = container.resolve(AIService)
```

## Configuration Management

Configuration is managed through environment variables and/or configuration files, with the ability to override defaults:

```python
# Environment-based configuration
config = EnvironmentConfigManager(prefix="ZENDESK_AI_")

# File-based configuration
config = JsonFileConfigManager("config.json")

# Get configuration values
api_key = config.get("api_key")
```

## Error Handling

The application uses a comprehensive error handling strategy with specific exception types and retry mechanisms:

```python
# Using retry decorator
@with_retry(max_retries=3, retry_on=[ConnectionError, TimeoutError])
def fetch_data():
    # Implementation

# Using retry strategy
retry_strategy = ExponentialBackoffRetryStrategy(max_retries=3)
result = retry_strategy.execute(fetch_data)
```

## Refactoring Approach

The refactoring is being done incrementally to minimize disruption:

1. **Phase 1**: Establish abstractions and interfaces
2. **Phase 2**: Refactor infrastructure components
3. **Phase 3**: Refactor application logic
4. **Phase 4**: Refactor presentation layer

Each phase is tested thoroughly before proceeding to the next.

## Testing Strategy

The application is tested at multiple levels:

- **Unit Tests** - Test individual components in isolation
- **Integration Tests** - Test interactions between components
- **Functional Tests** - Test end-to-end functionality
- **Performance Tests** - Test performance characteristics

Tests use mocks and stubs to isolate the system under test from external dependencies.
