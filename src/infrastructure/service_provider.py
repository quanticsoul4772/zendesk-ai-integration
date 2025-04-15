"""
Service Provider

This module provides a service provider for dependency injection in the application.
"""

import logging
import os
from typing import Dict, Any, Optional, Type, TypeVar, cast

from src.infrastructure.utils.dependency_injection import container
from src.infrastructure.utils.config_manager import EnvironmentConfigManager, JsonFileConfigManager
from src.infrastructure.repositories.zendesk_repository import ZendeskRepository
from src.infrastructure.repositories.mongodb_repository import MongoDBRepository
from src.infrastructure.external_services.openai_service import OpenAIService
from src.infrastructure.external_services.claude_service import ClaudeService
from src.infrastructure.cache.zendesk_cache_adapter import ZendeskCacheManager

from src.domain.interfaces.repository_interfaces import TicketRepository, AnalysisRepository, ViewRepository
from src.domain.interfaces.ai_service_interfaces import AIService, EnhancedAIService
from src.domain.interfaces.service_interfaces import TicketAnalysisService, ReportingService, WebhookService, SchedulerService
from src.domain.interfaces.cache_interfaces import CacheManager

from src.application.services.ticket_analysis_service import TicketAnalysisServiceImpl
from src.application.services.reporting_service import ReportingServiceImpl
from src.application.services.webhook_service import WebhookServiceImpl
from src.application.services.scheduler_service import SchedulerServiceImpl

from src.application.use_cases.analyze_ticket_use_case import AnalyzeTicketUseCase
from src.application.use_cases.generate_report_use_case import GenerateReportUseCase

# Set up logging
logger = logging.getLogger(__name__)

T = TypeVar('T')


class ServiceProvider:
    """
    Service provider for dependency injection.
    
    This class manages the creation and lifetime of service instances
    and provides methods to access them.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the service provider.
        
        Args:
            config_file: Optional path to a configuration file
        """
        self.config = self._create_config_manager(config_file)
        self._initialized = False
        
        # Initialize the container with services
        self._initialize_container()
    
    def _create_config_manager(self, config_file: Optional[str] = None) -> Any:
        """
        Create a configuration manager.
        
        Args:
            config_file: Optional path to a configuration file
            
        Returns:
            Configuration manager instance
        """
        # Create an environment-based config manager with a prefix
        env_config = EnvironmentConfigManager(prefix="ZENDESK_AI_")
        
        # If a config file is provided, create a file-based config manager
        if config_file:
            file_config = JsonFileConfigManager(config_file)
            
            # Merge the configurations, with file taking precedence
            for key, value in file_config.get_all().items():
                env_config.set(key, value)
        
        return env_config
    
    def _initialize_container(self) -> None:
        """Initialize the dependency injection container."""
        if self._initialized:
            return
        
        # Register configuration
        container.register_instance(Any, self.config, "config")
        
        # Register repositories
        self._register_repositories()
        
        # Register external services
        self._register_external_services()
        
        # Register application services
        self._register_application_services()
        
        # Register use cases
        self._register_use_cases()
        
        # Register utilities
        self._register_utilities()
        
        self._initialized = True
        logger.info("Service provider initialized")
    
    def _register_repositories(self) -> None:
        """Register repository implementations."""
        # Create cache manager
        cache_manager = ZendeskCacheManager()
        container.register_instance(CacheManager, cache_manager)
        
        # Create ZendeskRepository
        zendesk_repository = ZendeskRepository(cache_manager=cache_manager)
        container.register_instance(TicketRepository, zendesk_repository)
        container.register_instance(ViewRepository, zendesk_repository)
        
        # Create MongoDBRepository
        mongodb_repository = MongoDBRepository()
        container.register_instance(AnalysisRepository, mongodb_repository)
    
    def _register_external_services(self) -> None:
        """Register external service implementations."""
        # Create OpenAIService
        openai_service = OpenAIService()
        container.register_instance(AIService, openai_service, "openai")
        
        # Create ClaudeService
        claude_service = ClaudeService()
        container.register_instance(AIService, claude_service, "claude")
        container.register_instance(EnhancedAIService, claude_service)
    
    def _register_application_services(self) -> None:
        """Register application service implementations."""
        # Get repositories
        ticket_repository = container.resolve(TicketRepository)
        analysis_repository = container.resolve(AnalysisRepository)
        view_repository = container.resolve(ViewRepository)
        
        # Get AI service
        claude_service = container.resolve(AIService, "claude")
        
        # Create TicketAnalysisService
        ticket_analysis_service = TicketAnalysisServiceImpl(
            ticket_repository=ticket_repository,
            analysis_repository=analysis_repository,
            ai_service=claude_service
        )
        container.register_instance(TicketAnalysisService, ticket_analysis_service)
        
        # Create ReportingService
        reporting_service = ReportingServiceImpl(
            ticket_repository=ticket_repository,
            analysis_repository=analysis_repository,
            view_repository=view_repository,
            sentiment_reporter=None,  # TODO: Implement reporters
            hardware_reporter=None,
            pending_reporter=None,
            ticket_analysis_service=ticket_analysis_service
        )
        container.register_instance(ReportingService, reporting_service)
        
        # Create WebhookService
        webhook_service = WebhookServiceImpl(
            ticket_repository=ticket_repository,
            analysis_repository=analysis_repository,
            ticket_analysis_service=ticket_analysis_service
        )
        container.register_instance(WebhookService, webhook_service)
        
        # Create SchedulerService
        scheduler_service = SchedulerServiceImpl()
        container.register_instance(SchedulerService, scheduler_service)
    
    def _register_use_cases(self) -> None:
        """Register use case implementations."""
        # Get dependencies
        ticket_repository = container.resolve(TicketRepository)
        ticket_analysis_service = container.resolve(TicketAnalysisService)
        reporting_service = container.resolve(ReportingService)
        
        # Create AnalyzeTicketUseCase
        analyze_ticket_use_case = AnalyzeTicketUseCase(
            ticket_repository=ticket_repository,
            ticket_analysis_service=ticket_analysis_service
        )
        container.register_instance(AnalyzeTicketUseCase, analyze_ticket_use_case)
        
        # Create GenerateReportUseCase
        generate_report_use_case = GenerateReportUseCase(
            reporting_service=reporting_service
        )
        container.register_instance(GenerateReportUseCase, generate_report_use_case)
    
    def _register_utilities(self) -> None:
        """Register utility implementations."""
        # TODO: Register any utility implementations
        pass
    
    def get_config(self) -> Any:
        """
        Get the configuration manager.
        
        Returns:
            Configuration manager instance
        """
        return self.config
    
    def get_container(self):
        """
        Get the dependency injection container.
        
        Returns:
            Container instance
        """
        return container
    
    def get(self, interface_class: Type[T], name: Optional[str] = None) -> T:
        """
        Get a service by interface.
        
        Args:
            interface_class: Interface class
            name: Optional name for the registration
            
        Returns:
            Service instance
            
        Raises:
            KeyError: If the service is not registered
        """
        return container.resolve(interface_class, name)
    
    # Convenience methods for common services
    
    def get_ticket_repository(self) -> TicketRepository:
        """
        Get the ticket repository.
        
        Returns:
            Ticket repository instance
        """
        return self.get(TicketRepository)
    
    def get_analysis_repository(self) -> AnalysisRepository:
        """
        Get the analysis repository.
        
        Returns:
            Analysis repository instance
        """
        return self.get(AnalysisRepository)
    
    def get_view_repository(self) -> ViewRepository:
        """
        Get the view repository.
        
        Returns:
            View repository instance
        """
        return self.get(ViewRepository)
    
    def get_ai_service(self, use_claude: bool = True) -> AIService:
        """
        Get the AI service.
        
        Args:
            use_claude: Whether to use Claude (default) or OpenAI
            
        Returns:
            AI service instance
        """
        if use_claude:
            return self.get(AIService, "claude")
        else:
            return self.get(AIService, "openai")
    
    def get_enhanced_ai_service(self) -> EnhancedAIService:
        """
        Get the enhanced AI service.
        
        Returns:
            Enhanced AI service instance
        """
        return self.get(EnhancedAIService)
    
    def get_ticket_analysis_service(self) -> TicketAnalysisService:
        """
        Get the ticket analysis service.
        
        Returns:
            Ticket analysis service instance
        """
        return self.get(TicketAnalysisService)
    
    def get_reporting_service(self) -> ReportingService:
        """
        Get the reporting service.
        
        Returns:
            Reporting service instance
        """
        return self.get(ReportingService)
    
    def get_webhook_service(self) -> WebhookService:
        """
        Get the webhook service.
        
        Returns:
            Webhook service instance
        """
        return self.get(WebhookService)
    
    def get_scheduler_service(self) -> SchedulerService:
        """
        Get the scheduler service.
        
        Returns:
            Scheduler service instance
        """
        return self.get(SchedulerService)
    
    def get_analyze_ticket_use_case(self) -> AnalyzeTicketUseCase:
        """
        Get the analyze ticket use case.
        
        Returns:
            Analyze ticket use case instance
        """
        return self.get(AnalyzeTicketUseCase)
    
    def get_generate_report_use_case(self) -> GenerateReportUseCase:
        """
        Get the generate report use case.
        
        Returns:
            Generate report use case instance
        """
        return self.get(GenerateReportUseCase)
    
    def get_batch_analyzer(self) -> Any:
        """
        Get the batch analyzer service.
        
        Returns:
            Batch analyzer instance
        """
        # TODO: Implement BatchAnalyzer
        return None
    
    def get_webhook_server(self) -> Any:
        """
        Get the webhook server.
        
        Returns:
            Webhook server instance
        """
        # TODO: Implement WebhookServer
        return None
