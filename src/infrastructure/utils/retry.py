"""
Retry Utilities

This module provides utilities for retrying operations that might fail.
"""

import functools
import logging
import random
import time
from typing import Callable, List, Optional, Type, TypeVar, Union

from src.domain.interfaces.utility_interfaces import RetryStrategy

T = TypeVar('T')


class ExponentialBackoffRetryStrategy(RetryStrategy):
    """
    Implements exponential backoff retry strategy with jitter.
    
    This strategy retries the operation with an exponentially increasing
    delay between retries, plus a random jitter to avoid thundering herd problem.
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        retry_on: Union[Type[Exception], List[Type[Exception]]] = Exception,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        jitter: bool = True,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the retry strategy.
        
        Args:
            max_retries: Maximum number of retry attempts
            retry_on: Exception type(s) that should trigger a retry
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds
            jitter: Whether to add jitter to the delay
            logger: Logger instance
        """
        self.max_retries = max_retries
        self.retry_on = retry_on if isinstance(retry_on, list) else [retry_on]
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter
        self.logger = logger or logging.getLogger(__name__)
    
    def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute a function with retry logic.
        
        Args:
            func: Function to execute
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Result of the function
            
        Raises:
            Exception: If all retries fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):  # +1 for the initial attempt
            try:
                return func(*args, **kwargs)
            except tuple(self.retry_on) as e:
                last_exception = e
                
                # If this was the last attempt, don't retry
                if attempt >= self.max_retries:
                    break
                    
                # Calculate delay with exponential backoff
                delay = min(self.max_delay, self.base_delay * (2 ** attempt))
                
                # Add jitter if enabled
                if self.jitter:
                    jitter_amount = random.uniform(0, delay / 2)
                    delay += jitter_amount
                
                self.logger.warning(
                    f"Retry {attempt+1}/{self.max_retries} after {delay:.2f}s due to: {e}"
                )
                
                # Wait before retrying
                time.sleep(delay)
        
        # If we've exhausted all retries
        if last_exception:
            self.logger.error(f"All {self.max_retries} retry attempts failed")
            raise last_exception
            
        # This should never happen but just in case
        raise RuntimeError("Unexpected error in retry strategy")
    
    def get_retry_count(self) -> int:
        """
        Get the maximum number of retries.
        
        Returns:
            Maximum retry count
        """
        return self.max_retries
    
    def get_retry_exceptions(self) -> List[Type[Exception]]:
        """
        Get the exceptions that trigger a retry.
        
        Returns:
            List of exception types
        """
        return self.retry_on


def with_retry(
    max_retries: int = 3,
    retry_on: Union[Type[Exception], List[Type[Exception]]] = Exception,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    jitter: bool = True,
    logger: Optional[logging.Logger] = None
):
    """
    Decorator for retrying a function when it raises specified exceptions.
    
    Args:
        max_retries: Maximum number of retry attempts
        retry_on: Exception type(s) that should trigger a retry
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        jitter: Whether to add jitter to the delay
        logger: Logger instance
        
    Returns:
        Decorated function
    """
    retry_strategy = ExponentialBackoffRetryStrategy(
        max_retries=max_retries,
        retry_on=retry_on,
        base_delay=base_delay,
        max_delay=max_delay,
        jitter=jitter,
        logger=logger
    )
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return retry_strategy.execute(func, *args, **kwargs)
        return wrapper
    
    return decorator
