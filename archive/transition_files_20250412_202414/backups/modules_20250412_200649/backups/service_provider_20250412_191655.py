"""
Service Provider

This module provides a service provider/factory for creating and managing service instances.
It wires together the application components and dependencies.
"""

import logging
import os
from typing import Dict, Any, Optional

from src.domain.interfaces.repository_interfaces import TicketRepository, AnalysisRepository, ViewRepository
from src.domain.interfaces.ai_service_interfaces import AIService, EnhancedAIService
from src.domain.interfaces.service_interfaces import (
    TicketAnalysisService, 
    ReportingService, 
    WebhookService,
    SchedulerService
)
from src.domain.interfaces.reporter_interfaces import SentimentReporter, HardwareReporter, PendingReporter

from src.infrastructure.repositories.zendesk_repository import ZendeskRepository
from src.infrastructure.repositories.mongodb_repository import MongoDBRepository
from src.infrastructure.external_services.openai_service import OpenAIService
from src.infrastructure.external_services.claude_service import ClaudeService
from src.infrastructure.cache.zendesk_cache_adapter import ZendeskCacheManager
from src.infrastructure.utils.config_manager import EnvironmentConfigManager, JsonFileConfigManager

from src.application.services.ticket_analysis_service import TicketAnalysisServiceImpl
from src.application.services.reporting_service import ReportingServiceImpl
from src.application.services.webhook_service import WebhookServiceImpl
from src.application.services.scheduler_service import SchedulerServiceImpl
from src.application.use_cases.generate_report_use_case import GenerateReportUseCase

# Set up logging
logger = logging.getLogger(__name__)


class ServiceProvider:
    """
    Service provider/factory for application components.
    
    This class manages the creation and caching of service instances
    and wires together dependencies.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the service provider.
        
        Args:
            config_file: Optional path to a configuration file
        """
        # Initialize configuration
        self.config = self._create_config(config_file)
        
        # Initialize service cache
        self._services: Dict[str, Any] = {}
    
    def _create_config(self, config_file: Optional[str]) -> Any:
        """
        Create and initialize the configuration manager.
        
        Args:
            config_file: Optional path to a configuration file
            
        Returns:
            ConfigManager instance
        """
        # Create environment config
        env_config = EnvironmentConfigManager(prefix="ZENDESK_AI_", default_values={
            "ai_service": "openai",  # or "claude"
            "mongodb_uri": "mongodb://localhost:27017",
            "mongodb_db_name": "zendesk_analytics",
            "mongodb_collection_name": "ticket_analysis",
            "reports_dir": "./reports",
            "log_level": "INFO"
        })
        
        # If config file is provided, load it
        if config_file:
            file_config = JsonFileConfigManager(config_file)
            
            # Merge file config into environment config
            for key, value in file_config.get_all().items():
                env_config.set(key, value)
        
        return env_config
    
    def get_ticket_repository(self) -> TicketRepository:
        """
        Get the ticket repository.
        
        Returns:
            Ticket repository instance
        """
        if "ticket_repository" not in self._services:
            cache_manager = self.get_cache_manager()
            zendesk_repo = ZendeskRepository(cache_manager=cache_manager)
            self._services["ticket_repository"] = zendesk_repo
        
        return self._services["ticket_repository"]
    
    def get_analysis_repository(self) -> AnalysisRepository:
        """
        Get the analysis repository.
        
        Returns:
            Analysis repository instance
        """
        if "analysis_repository" not in self._services:
            mongodb_uri = self.config.get("mongodb_uri")
            db_name = self.config.get("mongodb_db_name")
            collection_name = self.config.get("mongodb_collection_name")
            
            mongo_repo = MongoDBRepository()
            self._services["analysis_repository"] = mongo_repo
        
        return self._services["analysis_repository"]
    
    def get_view_repository(self) -> ViewRepository:
        """
        Get the view repository.
        
        Returns:
            View repository instance
        """
        # The ZendeskRepository also implements ViewRepository
        return self.get_ticket_repository()
    
    def get_ai_service(self) -> AIService:
        """
        Get the AI service.
        
        Returns:
            AI service instance
        """
        if "ai_service" not in self._services:
            ai_service_type = self.config.get("ai_service", "openai")
            
            if ai_service_type == "claude":
                api_key = self.config.get("claude_api_key") or os.getenv("ANTHROPIC_API_KEY")
                model = self.config.get("claude_model", "claude-3-haiku-20240307")
                
                claude_service = ClaudeService(api_key=api_key, model=model)
                self._services["ai_service"] = claude_service
            else:
                api_key = self.config.get("openai_api_key") or os.getenv("OPENAI_API_KEY")
                model = self.config.get("openai_model", "gpt-4o-mini")
                
                openai_service = OpenAIService(api_key=api_key, model=model)
                self._services["ai_service"] = openai_service
        
        return self._services["ai_service"]
    
    def get_enhanced_ai_service(self) -> EnhancedAIService:
        """
        Get the enhanced AI service.
        
        Returns:
            EnhancedAIService instance
        """
        if "enhanced_ai_service" not in self._services:
            # Check if the AI service is already an EnhancedAIService
            ai_service = self.get_ai_service()
            
            if isinstance(ai_service, EnhancedAIService):
                self._services["enhanced_ai_service"] = ai_service
            else:
                # If not, create a Claude service (which implements EnhancedAIService)
                api_key = self.config.get("claude_api_key") or os.getenv("ANTHROPIC_API_KEY")
                model = self.config.get("claude_model", "claude-3-haiku-20240307")
                
                claude_service = ClaudeService(api_key=api_key, model=model)
                self._services["enhanced_ai_service"] = claude_service
        
        return self._services["enhanced_ai_service"]
    
    def get_cache_manager(self) -> ZendeskCacheManager:
        """
        Get the cache manager.
        
        Returns:
            Cache manager instance
        """
        if "cache_manager" not in self._services:
            cache_manager = ZendeskCacheManager()
            self._services["cache_manager"] = cache_manager
        
        return self._services["cache_manager"]
    
    def get_ticket_analysis_service(self) -> TicketAnalysisService:
        """
        Get the ticket analysis service.
        
        Returns:
            Ticket analysis service instance
        """
        if "ticket_analysis_service" not in self._services:
            ticket_repo = self.get_ticket_repository()
            analysis_repo = self.get_analysis_repository()
            ai_service = self.get_ai_service()
            
            service = TicketAnalysisServiceImpl(
                ticket_repository=ticket_repo,
                analysis_repository=analysis_repo,
                ai_service=ai_service
            )
            
            self._services["ticket_analysis_service"] = service
        
        return self._services["ticket_analysis_service"]
    
    def get_reporting_service(self) -> ReportingService:
        """
        Get the reporting service.
        
        Returns:
            Reporting service instance
        """
        if "reporting_service" not in self._services:
            ticket_repo = self.get_ticket_repository()
            analysis_repo = self.get_analysis_repository()
            view_repo = self.get_view_repository()
            
            # Import the reporters
            from src.presentation.reporters.sentiment_reporter import SentimentReporterImpl
            from src.presentation.reporters.hardware_reporter import HardwareReporterImpl
            from src.presentation.reporters.pending_reporter import PendingReporterImpl
            
            sentiment_reporter = SentimentReporterImpl()
            hardware_reporter = HardwareReporterImpl()
            pending_reporter = PendingReporterImpl()
            
            service = ReportingServiceImpl(
                ticket_repository=ticket_repo,
                analysis_repository=analysis_repo,
                view_repository=view_repo,
                sentiment_reporter=sentiment_reporter,
                hardware_reporter=hardware_reporter,
                pending_reporter=pending_reporter,
                ticket_analysis_service=self.get_ticket_analysis_service()
            )
            
            self._services["reporting_service"] = service
        
        return self._services["reporting_service"]
    
    def get_webhook_service(self) -> WebhookService:
        """
        Get the webhook service.
        
        Returns:
            Webhook service instance
        """
        if "webhook_service" not in self._services:
            ticket_repo = self.get_ticket_repository()
            analysis_repo = self.get_analysis_repository()
            ticket_analysis_service = self.get_ticket_analysis_service()
            
            service = WebhookServiceImpl(
                ticket_repository=ticket_repo,
                analysis_repository=analysis_repo,
                ticket_analysis_service=ticket_analysis_service
            )
            
            # Set comment preference from config
            add_comments = self.config.get("add_comments", False)
            service.set_comment_preference(add_comments)
            
            self._services["webhook_service"] = service
        
        return self._services["webhook_service"]
    
    def get_scheduler_service(self) -> SchedulerService:
        """
        Get the scheduler service.
        
        Returns:
            Scheduler service instance
        """
        if "scheduler_service" not in self._services:
            service = SchedulerServiceImpl()
            self._services["scheduler_service"] = service
        
        return self._services["scheduler_service"]
        
    def get_generate_report_use_case(self):
        """
        Get the generate report use case.
        
        Returns:
            GenerateReportUseCase instance
        """
        if "generate_report_use_case" not in self._services:
            # Get the required dependency
            reporting_service = self.get_reporting_service()
            
            # Create the use case
            use_case = GenerateReportUseCase(
                reporting_service=reporting_service
            )
            
            self._services["generate_report_use_case"] = use_case
        
        return self._services["generate_report_use_case"]
