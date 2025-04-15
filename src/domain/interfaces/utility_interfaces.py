"""
Utility Interfaces

This module defines interfaces for utility classes and functions.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

T = TypeVar('T')


class RetryStrategy(ABC):
    """Interface for retry strategies."""
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def get_retry_count(self) -> int:
        """
        Get the maximum number of retries.
        
        Returns:
            Maximum retry count
        """
        pass
    
    @abstractmethod
    def get_retry_exceptions(self) -> List[type]:
        """
        Get the exceptions that trigger a retry.
        
        Returns:
            List of exception types
        """
        pass


class ConfigManager(ABC):
    """Interface for configuration management."""
    
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        pass
    
    @abstractmethod
    def load(self, filepath: str) -> bool:
        """
        Load configuration from a file.
        
        Args:
            filepath: Path to configuration file
            
        Returns:
            Success indicator
        """
        pass
    
    @abstractmethod
    def save(self, filepath: str) -> bool:
        """
        Save configuration to a file.
        
        Args:
            filepath: Path to save configuration to
            
        Returns:
            Success indicator
        """
        pass
    
    @abstractmethod
    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration values.
        
        Returns:
            Dictionary with all configuration values
        """
        pass


class LoggingManager(ABC):
    """Interface for logging management."""
    
    @abstractmethod
    def configure(self, level: str, log_file: Optional[str] = None) -> None:
        """
        Configure logging settings.
        
        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional path to log file
        """
        pass
    
    @abstractmethod
    def get_logger(self, name: str) -> Any:
        """
        Get a logger for a specific module.
        
        Args:
            name: Logger name
            
        Returns:
            Logger instance
        """
        pass
    
    @abstractmethod
    def set_level(self, level: str) -> None:
        """
        Set the global logging level.
        
        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        pass


class MetricsCollector(ABC):
    """Interface for metrics collection."""
    
    @abstractmethod
    def increment(self, metric_name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None) -> None:
        """
        Increment a counter metric.
        
        Args:
            metric_name: Name of the metric
            value: Value to increment by
            tags: Optional tags for the metric
        """
        pass
    
    @abstractmethod
    def timing(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """
        Record a timing metric.
        
        Args:
            metric_name: Name of the metric
            value: Timing value in milliseconds
            tags: Optional tags for the metric
        """
        pass
    
    @abstractmethod
    def gauge(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """
        Set a gauge metric.
        
        Args:
            metric_name: Name of the metric
            value: Gauge value
            tags: Optional tags for the metric
        """
        pass
    
    @abstractmethod
    def histogram(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """
        Record a histogram value.
        
        Args:
            metric_name: Name of the metric
            value: Histogram value
            tags: Optional tags for the metric
        """
        pass
