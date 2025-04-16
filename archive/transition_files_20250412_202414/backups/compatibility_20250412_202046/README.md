# Compatibility Layer

This directory contains compatibility adapters to help with the transition from legacy components to the new architecture.

## Purpose

The compatibility adapters provide interfaces that match the legacy APIs but use the new implementations internally. This allows for a gradual migration without breaking existing code that depends on the legacy components.

## Adapter Pattern

These adapters implement the Adapter pattern, which allows objects with incompatible interfaces to work together. In this case, we're adapting the new implementations to present the legacy interfaces that existing code expects.

## Usage

To use a compatibility adapter:

1. Find where the legacy component is imported
2. Replace the import with the corresponding adapter
3. The code should continue to work as before

For example:

```python
# Before
from src.modules.zendesk_client import ZendeskClient

# After
from src.infrastructure.compatibility.zendesk_adapter import ZendeskClientAdapter as ZendeskClient
```

## Available Adapters

- `zendesk_adapter.py`: Adapts `ZendeskRepository` to provide `ZendeskClient` interface
- `ai_analyzer_adapter.py`: Adapts `AIService` implementations to provide `AIAnalyzer` interface
- `db_repository_adapter.py`: Adapts `MongoDBRepository` to provide legacy `DBRepository` interface
- `webhook_adapter.py`: Adapts `WebhookHandler` to provide `WebhookServer` interface
- `scheduler_adapter.py`: Adapts `SchedulerService` to provide legacy `TaskScheduler` interface
- `reporter_adapter.py`: Adapts new reporters to provide legacy reporter interfaces
- `service_provider_adapter.py`: Adapts new dependency injection system to provide legacy `ServiceProvider` interface

## Implementation Notes

Each adapter should:

1. Implement the same public interface as the legacy component
2. Use the new implementation internally
3. Map between legacy and new data formats as needed
4. Log warnings to indicate that legacy interfaces are being used (in debug mode)
5. Include detailed documentation on how to migrate to the new interfaces

## Migration Strategy

The adapters are intended as temporary solutions during the migration process. Once all code has been updated to use the new interfaces directly, the adapters should be removed.

The recommended migration process is:

1. Use the adapter as a drop-in replacement for legacy components
2. Update the code to use the new interfaces when convenient (one file at a time)
3. Once all direct references to legacy components are removed, remove the legacy files
4. Once all adapter uses are replaced with direct uses of new components, remove the adapters

## Testing

Each adapter should have thorough tests that verify:

1. It correctly implements the legacy interface
2. It correctly uses the new implementation
3. It handles all edge cases and error conditions appropriately

## Service Provider Adapter

The `service_provider_adapter.py` file provides a special adapter that acts as a bridge between the legacy service provider and the new dependency injection system. It offers both legacy methods (like `get_zendesk_client()`) and new methods (like `get_ticket_repository()`), making it a perfect transition tool.

Using the service provider adapter:

```python
# Before
from src.modules.service_provider import ServiceProvider
service_provider = ServiceProvider()
zendesk_client = service_provider.get_zendesk_client()

# After
from src.infrastructure.compatibility.service_provider_adapter import ServiceProviderAdapter
service_provider = ServiceProviderAdapter()
zendesk_client = service_provider.get_zendesk_client()  # Returns an adapter
# Or use the new interfaces directly:
ticket_repository = service_provider.get_ticket_repository()
```

## Logging

All adapters include detailed logging to help track which legacy interfaces are still being used. This can help prioritize which parts of the codebase to update next.