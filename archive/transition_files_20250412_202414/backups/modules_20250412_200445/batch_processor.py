"""
Batch Processor Module

This module is a re-export of the batch processor adapter for backward compatibility.
"""

from src.infrastructure.compatibility.batch_processor_adapter import BatchProcessor

# Re-export the BatchProcessor class
__all__ = ['BatchProcessor']
