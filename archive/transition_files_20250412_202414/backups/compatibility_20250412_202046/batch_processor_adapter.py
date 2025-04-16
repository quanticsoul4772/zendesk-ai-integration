"""
Batch Processor Adapter

This module provides an adapter that presents a BatchProcessor interface
but uses the new batch processing implementation internally.
"""

import logging
import concurrent.futures
from typing import List, Callable, Any, Optional, Union

# Set up logging
logger = logging.getLogger(__name__)


class BatchProcessor:
    """
    Batch processor that processes items in parallel.
    
    This adapter maintains the interface of the legacy BatchProcessor but uses
    the new concurrent processing implementation.
    """
    
    def __init__(self, max_workers=None):
        """
        Initialize the batch processor.
        
        Args:
            max_workers: Maximum number of worker threads to use
        """
        self.max_workers = max_workers
        logger.debug(f"BatchProcessor initialized with max_workers={max_workers}")
    
    def process_batch(self, items, processor_func, *args, **kwargs):
        """
        Process a batch of items in parallel.
        
        Args:
            items: List of items to process
            processor_func: Function to call for each item
            *args: Additional positional arguments to pass to the processor function
            **kwargs: Additional keyword arguments to pass to the processor function
            
        Returns:
            List of results, one for each input item
        """
        if not items:
            logger.debug("Empty batch, returning empty list")
            return []
        
        logger.debug(f"Processing batch of {len(items)} items with max_workers={self.max_workers}")
        
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for item in items:
                future = executor.submit(processor_func, item, *args, **kwargs)
                futures.append(future)
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as exc:
                    logger.error(f"Item processing failed: {exc}")
                    results.append(None)
        
        return results
    
    def map(self, func, items, *args, **kwargs):
        """
        Map a function over a list of items in parallel.
        
        Args:
            func: Function to apply to each item
            items: List of items to process
            *args: Additional positional arguments to pass to the function
            **kwargs: Additional keyword arguments to pass to the function
            
        Returns:
            List of results, one for each input item
        """
        return self.process_batch(items, func, *args, **kwargs)
