"""
Service Provider Adapter

This module provides an adapter that presents a legacy ServiceProvider interface
but uses the new dependency injection system internally.
"""

import logging
from typing import Dict, List, Any, Optional, Union

from src.infrastructure.utils.dependency_injection import DependencyContainer
from src.infrastructure.compatibility.zendesk_adapter import ZendeskClientAdapter
from src.infrastructure.compatibility.ai_analyzer_adapter import AIAnalyzerAdapter
from src.infrastructure.compatibility.db_repository_adapter import DBRepositoryAdapter
from src.infrastructure.compatibility.webhook_adapter import WebhookServerAdapter
from src.infrastructure.compatibility.scheduler_adapter import SchedulerAdapter
from src.infrastructure.compatibility.reporter_adapter import (
    SentimentReporterAdapter,
    HardwareReporterAdapter,
    PendingReporterAdapter
)

# Set up logging
logger = logging.getLogger(__name__)


class ServiceProviderAdapter:
    """
    Adapter that presents a legacy ServiceProvider interface but uses the
    new dependency injection system internally.
    
    This adapter helps with the transition from the legacy ServiceProvider to the
    new dependency injection-based implementation.
    """
    
    def __init__(self, service_container=None):
        """
        Initialize the adapter.
        
        Args:
            service_container: Optional DependencyContainer instance
        """
        self._container = service_container or DependencyContainer()
        
        # Cache for adapter instances
        self._adapters = {}
        
        logger.debug("ServiceProviderAdapter initialized")
    
    def _get_adapter(self, adapter_class, *args, **kwargs):
        """
        Get or create an adapter instance.
        
        Args:
            adapter_class: Adapter class to instantiate
            *args: Positional arguments for the adapter constructor
            **kwargs: Keyword arguments for the adapter constructor
            
        Returns:
            Adapter instance
        """
        adapter_name = adapter_class.__name__
        
        if adapter_name not in self._adapters:
            self._adapters[adapter_name] = adapter_class(*args, **kwargs)
            logger.debug(f"Created new {adapter_name} instance")
        
        return self._adapters[adapter_name]
    
    def get_zendesk_client(self):
        """
        Get a ZendeskClient instance (adapter).
        
        Returns:
            ZendeskClientAdapter instance
        """
        logger.debug("ServiceProviderAdapter.get_zendesk_client called")
        
        ticket_repository = self._container.resolve('ticket_repository')
        view_repository = self._container.resolve('view_repository')
        
        return self._get_adapter(ZendeskClientAdapter, repository=ticket_repository)
    
    def get_ai_analyzer(self):
        """
        Get an AIAnalyzer instance (adapter).
        
        Returns:
            AIAnalyzerAdapter instance
        """
        logger.debug("ServiceProviderAdapter.get_ai_analyzer called")
        
        ticket_analysis_service = self._container.resolve('ticket_analysis_service')
        claude_service = self._container.resolve('claude_service')
        openai_service = self._container.resolve('openai_service')
        
        return self._get_adapter(
            AIAnalyzerAdapter,
            ticket_analysis_service=ticket_analysis_service,
            claude_service=claude_service,
            openai_service=openai_service
        )
    
    def get_db_repository(self):
        """
        Get a DBRepository instance (adapter).
        
        Returns:
            DBRepositoryAdapter instance
        """
        logger.debug("ServiceProviderAdapter.get_db_repository called")
        
        analysis_repository = self._container.resolve('analysis_repository')
        
        return self._get_adapter(DBRepositoryAdapter, repository=analysis_repository)
    
    def get_webhook_server(self):
        """
        Get a WebhookServer instance (adapter).
        
        Returns:
            WebhookServerAdapter instance
        """
        logger.debug("ServiceProviderAdapter.get_webhook_server called")
        
        webhook_service = self._container.resolve('webhook_service')
        webhook_handler = self._container.resolve('webhook_handler')
        
        adapter = self._get_adapter(
            WebhookServerAdapter,
            webhook_service=webhook_service,
            webhook_handler=webhook_handler
        )
        
        # Configure adapter with other services
        adapter.set_services(
            self.get_zendesk_client(),
            self.get_ai_analyzer(),
            self.get_db_repository()
        )
        
        return adapter
    
    def get_scheduler(self):
        """
        Get a TaskScheduler instance (adapter).
        
        Returns:
            SchedulerAdapter instance
        """
        logger.debug("ServiceProviderAdapter.get_scheduler called")
        
        scheduler_service = self._container.resolve('scheduler_service')
        
        adapter = self._get_adapter(SchedulerAdapter, scheduler_service=scheduler_service)
        
        # Configure adapter with other services
        adapter.set_services(
            self.get_zendesk_client(),
            self.get_ai_analyzer(),
            self.get_db_repository()
        )
        
        return adapter
    
    def get_sentiment_reporter(self):
        """
        Get a SentimentReporter instance (adapter).
        
        Returns:
            SentimentReporterAdapter instance
        """
        logger.debug("ServiceProviderAdapter.get_sentiment_reporter called")
        
        sentiment_reporter = self._container.resolve('sentiment_reporter')
        
        adapter = self._get_adapter(SentimentReporterAdapter, reporter=sentiment_reporter)
        
        # Configure adapter with other services
        adapter.set_services(
            self.get_zendesk_client(),
            self.get_ai_analyzer(),
            self.get_db_repository()
        )
        
        return adapter
    
    def get_hardware_reporter(self):
        """
        Get a HardwareReporter instance (adapter).
        
        Returns:
            HardwareReporterAdapter instance
        """
        logger.debug("ServiceProviderAdapter.get_hardware_reporter called")
        
        hardware_reporter = self._container.resolve('hardware_reporter')
        
        adapter = self._get_adapter(HardwareReporterAdapter, reporter=hardware_reporter)
        
        # Configure adapter with other services
        adapter.set_services(
            self.get_zendesk_client(),
            self.get_ai_analyzer(),
            self.get_db_repository()
        )
        
        return adapter
    
    def get_pending_reporter(self):
        """
        Get a PendingReporter instance (adapter).
        
        Returns:
            PendingReporterAdapter instance
        """
        logger.debug("ServiceProviderAdapter.get_pending_reporter called")
        
        pending_reporter = self._container.resolve('pending_reporter')
        
        adapter = self._get_adapter(PendingReporterAdapter, reporter=pending_reporter)
        
        # Configure adapter with other services
        adapter.set_services(
            self.get_zendesk_client(),
            self.get_ai_analyzer(),
            self.get_db_repository()
        )
        
        return adapter
    
    # Bridge methods for new service access
    
    def get_ticket_repository(self):
        """
        Get a TicketRepository instance.
        
        Returns:
            TicketRepository instance
        """
        logger.debug("ServiceProviderAdapter.get_ticket_repository called")
        
        return self._container.resolve('ticket_repository')
    
    def get_view_repository(self):
        """
        Get a ViewRepository instance.
        
        Returns:
            ViewRepository instance
        """
        logger.debug("ServiceProviderAdapter.get_view_repository called")
        
        return self._container.resolve('view_repository')
    
    def get_analysis_repository(self):
        """
        Get an AnalysisRepository instance.
        
        Returns:
            AnalysisRepository instance
        """
        logger.debug("ServiceProviderAdapter.get_analysis_repository called")
        
        return self._container.resolve('analysis_repository')
    
    def get_ticket_analysis_service(self):
        """
        Get a TicketAnalysisService instance.
        
        Returns:
            TicketAnalysisService instance
        """
        logger.debug("ServiceProviderAdapter.get_ticket_analysis_service called")
        
        return self._container.resolve('ticket_analysis_service')
    
    def get_reporting_service(self):
        """
        Get a ReportingService instance.
        
        Returns:
            ReportingService instance
        """
        logger.debug("ServiceProviderAdapter.get_reporting_service called")
        
        return self._container.resolve('reporting_service')
    
    def get_webhook_service(self):
        """
        Get a WebhookService instance.
        
        Returns:
            WebhookService instance
        """
        logger.debug("ServiceProviderAdapter.get_webhook_service called")
        
        return self._container.resolve('webhook_service')
    
    def get_scheduler_service(self):
        """
        Get a SchedulerService instance.
        
        Returns:
            SchedulerService instance
        """
        logger.debug("ServiceProviderAdapter.get_scheduler_service called")
        
        return self._container.resolve('scheduler_service')
    
    def get_batch_analyzer(self):
        """
        Get a BatchAnalyzer instance.
        
        Returns:
            BatchAnalyzer instance
        """
        logger.debug("ServiceProviderAdapter.get_batch_analyzer called")
        
        return self._container.resolve('batch_analyzer')
    
    def get_analyze_ticket_use_case(self):
        """
        Get an AnalyzeTicketUseCase instance.
        
        Returns:
            AnalyzeTicketUseCase instance
        """
        logger.debug("ServiceProviderAdapter.get_analyze_ticket_use_case called")
        
        return self._container.resolve('analyze_ticket_use_case')
    
    def get_generate_report_use_case(self):
        """
        Get a GenerateReportUseCase instance.
        
        Returns:
            GenerateReportUseCase instance
        """
        logger.debug("ServiceProviderAdapter.get_generate_report_use_case called")
        
        return self._container.resolve('generate_report_use_case')
