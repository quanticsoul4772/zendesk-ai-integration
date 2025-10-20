"""
Domain Package

This package contains the core domain model for the Zendesk AI Integration application.
It includes entities, value objects, and interfaces that define the domain.
"""

# Import entities for easier access
from src.domain.entities.ticket import Ticket
from src.domain.entities.ticket_analysis import TicketAnalysis, SentimentAnalysis

# Import interfaces for easier access
from src.domain.interfaces.ai_service_interfaces import (
    AIService,
    EnhancedAIService,
    AIServiceError,
    RateLimitError,
    TokenLimitError,
    ContentFilterError
)

from src.domain.interfaces.repository_interfaces import (
    TicketRepository,
    AnalysisRepository,
    ViewRepository
)

from src.domain.interfaces.service_interfaces import (
    TicketAnalysisService,
    ReportingService,
    WebhookService,
    SchedulerService
)

from src.domain.interfaces.reporter_interfaces import (
    Reporter,
    SentimentReporter,
    HardwareReporter,
    PendingReporter
)

from src.domain.interfaces.cache_interfaces import (
    Cache,
    CacheManager,
    CacheStatistics
)

from src.domain.interfaces.utility_interfaces import (
    RetryStrategy,
    ConfigManager,
    LoggingManager,
    MetricsCollector
)

__all__ = [
    # Entities
    'Ticket', 'TicketAnalysis', 'SentimentAnalysis',

    # AI Service Interfaces
    'AIService', 'EnhancedAIService', 'AIServiceError', 'RateLimitError',
    'TokenLimitError', 'ContentFilterError',

    # Repository Interfaces
    'TicketRepository', 'AnalysisRepository', 'ViewRepository',

    # Service Interfaces
    'TicketAnalysisService', 'ReportingService', 'WebhookService', 'SchedulerService',

    # Reporter Interfaces
    'Reporter', 'SentimentReporter', 'HardwareReporter', 'PendingReporter',

    # Cache Interfaces
    'Cache', 'CacheManager', 'CacheStatistics',

    # Utility Interfaces
    'RetryStrategy', 'ConfigManager', 'LoggingManager', 'MetricsCollector'
]
