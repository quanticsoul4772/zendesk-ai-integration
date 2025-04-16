"""
Interfaces Package

This package contains interfaces for the Zendesk AI Integration application.
"""

# Import all interfaces for easier access
from src.domain.interfaces.ai_service_interfaces import *
from src.domain.interfaces.repository_interfaces import *
from src.domain.interfaces.service_interfaces import *
from src.domain.interfaces.reporter_interfaces import *
from src.domain.interfaces.cache_interfaces import *
from src.domain.interfaces.utility_interfaces import *

__all__ = [
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
