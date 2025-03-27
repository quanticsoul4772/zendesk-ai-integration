"""
Batch Processor Module

This module provides functionality for batch processing operations
using thread pools to improve performance for I/O-bound operations.
"""

import concurrent.futures
import logging
from typing import List, Dict, Any, Callable, TypeVar, Generic
from tqdm import tqdm

# Set up logging
logger = logging.getLogger(__name__)

# Define generic type variables
T = TypeVar('T')  # Input item type
R = TypeVar('R')  # Result item type

class BatchProcessor:
    """
    Handles batch processing of operations using thread pools.
    Ideal for I/O-bound operations like API calls or network requests.
    """
    
    def __init__(self, max_workers: int = 5, batch_size: int = 10, 
                 show_progress: bool = True):
        """
        Initialize the batch processor.
        
        Args:
            max_workers: Maximum number of worker threads (default: 5)
            batch_size: Size of each batch for processing (default: 10)
            show_progress: Whether to show a progress bar (default: True)
        """
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.show_progress = show_progress
        
    def process_batch(self, items: List[T], process_func: Callable[[T], R], 
                      *args, **kwargs) -> List[R]:
        """
        Process items in batches using a ThreadPoolExecutor.
        
        Args:
            items: List of items to process
            process_func: Function to apply to each item
            *args: Additional positional arguments to pass to process_func
            **kwargs: Additional keyword arguments to pass to process_func
            
        Returns:
            List of processed results
        """
        results = []
        total_items = len(items)
        
        if total_items == 0:
            logger.warning("No items to process in batch")
            return results
            
        logger.info(f"Starting batch processing of {total_items} items with "
                   f"{self.max_workers} workers and batch size {self.batch_size}")
        
        # Create progress bar if enabled
        pbar = None
        if self.show_progress:
            pbar = tqdm(total=total_items, desc="Processing items")
        
        # Process items in batches
        for i in range(0, total_items, self.batch_size):
            batch = items[i:i+self.batch_size]
            batch_results = self._process_concurrent(
                batch, process_func, *args, **kwargs
            )
            results.extend(batch_results)
            
            # Update progress bar
            if pbar:
                pbar.update(len(batch))
                
            logger.info(f"Processed batch {i//self.batch_size + 1}/{(total_items-1)//self.batch_size + 1} "
                       f"({len(batch)} items)")
        
        # Close progress bar
        if pbar:
            pbar.close()
            
        logger.info(f"Completed batch processing of {total_items} items. "
                   f"Got {len(results)} results.")
        return results
        
    def _process_concurrent(self, items: List[T], process_func: Callable[[T], R], 
                           *args, **kwargs) -> List[R]:
        """
        Process a single batch concurrently using ThreadPoolExecutor.
        
        Args:
            items: List of items to process
            process_func: Function to apply to each item
            *args: Additional positional arguments to pass to process_func
            **kwargs: Additional keyword arguments to pass to process_func
            
        Returns:
            List of processed results
        """
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_item = {
                executor.submit(process_func, item, *args, **kwargs): item 
                for item in items
            }
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_item):
                item = future_to_item[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error processing item {item}: {e}", exc_info=True)
                    # Could add a placeholder for failed items here if needed
        
        return results
