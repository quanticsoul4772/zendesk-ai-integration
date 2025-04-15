"""
Compatibility Layer

This package provides adapters to help transition from legacy components
to the new clean architecture implementation.
"""

# Import all adapters for easy access
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
from src.infrastructure.compatibility.service_provider_adapter import ServiceProviderAdapter
from src.infrastructure.compatibility.batch_processor_adapter import BatchProcessor
from src.infrastructure.compatibility.report_generator_adapter import (
    generate_summary_report,
    generate_enhanced_summary_report,
    generate_hardware_report,
    generate_pending_report,
    get_summary_report_filename,
    get_enhanced_summary_report_filename,
    get_hardware_report_filename,
    get_pending_report_filename
)

# Convenience aliases to make migration easier
ZendeskClient = ZendeskClientAdapter
AIAnalyzer = AIAnalyzerAdapter
DBRepository = DBRepositoryAdapter
WebhookServer = WebhookServerAdapter
Scheduler = SchedulerAdapter
SentimentReporter = SentimentReporterAdapter
HardwareReporter = HardwareReporterAdapter
PendingReporter = PendingReporterAdapter
ServiceProvider = ServiceProviderAdapter
