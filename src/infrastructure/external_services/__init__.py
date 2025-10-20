"""
External Services Package

This package contains adapters for external services used by the Zendesk AI Integration application.
"""

from src.infrastructure.external_services.claude_service import ClaudeService
from src.infrastructure.external_services.openai_service import OpenAIService

__all__ = ['OpenAIService', 'ClaudeService']
