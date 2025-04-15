"""
Domain Exceptions

This module defines exceptions for the Zendesk AI Integration application domain.
"""

class DomainError(Exception):
    """Base exception for all domain errors."""
    pass


class EntityError(DomainError):
    """Base exception for entity related errors."""
    pass


class EntityNotFoundError(EntityError):
    """Raised when an entity is not found."""
    pass


class EntityValidationError(EntityError):
    """Raised when entity validation fails."""
    pass


class RepositoryError(DomainError):
    """Base exception for repository related errors."""
    pass


class ConnectionError(RepositoryError):
    """Raised when a connection to a repository fails."""
    pass


class QueryError(RepositoryError):
    """Raised when a query fails."""
    pass


class PersistenceError(RepositoryError):
    """Raised when data persistence fails."""
    pass


class ServiceError(DomainError):
    """Base exception for service related errors."""
    pass


class ConfigurationError(ServiceError):
    """Raised when service configuration is invalid."""
    pass


class ExternalServiceError(ServiceError):
    """Raised when communication with an external service fails."""
    pass


class ZendeskError(ExternalServiceError):
    """Raised when communication with Zendesk API fails."""
    pass


class AIServiceError(ExternalServiceError):
    """Base exception for AI service related errors."""
    pass


class RateLimitError(AIServiceError):
    """Raised when API rate limits are exceeded."""
    pass


class TokenLimitError(AIServiceError):
    """Raised when token limits are exceeded."""
    pass


class ContentFilterError(AIServiceError):
    """Raised when content violates AI service content policies."""
    pass


class AuthenticationError(ExternalServiceError):
    """Raised when authentication with an external service fails."""
    pass


class BusinessRuleError(DomainError):
    """Raised when a business rule is violated."""
    pass


class InvalidOperationError(DomainError):
    """Raised when an operation is invalid in the current context."""
    pass
