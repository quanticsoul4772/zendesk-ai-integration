"""
Cache Interfaces

This module defines interfaces for caching systems.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Pattern, Tuple


class CacheStatistics(ABC):
    """Interface for cache statistics."""
    
    @abstractmethod
    def record_hit(self, access_time: float = 0) -> None:
        """Record a cache hit."""
        pass
    
    @abstractmethod
    def record_miss(self, access_time: float = 0) -> None:
        """Record a cache miss."""
        pass
    
    @abstractmethod
    def get_hit_rate(self) -> float:
        """
        Get the cache hit rate.
        
        Returns:
            Float representing the hit rate (0-1)
        """
        pass
    
    @abstractmethod
    def get_average_access_time(self) -> float:
        """
        Get the average cache access time in milliseconds.
        
        Returns:
            Average access time in milliseconds
        """
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        Get all statistics as a dictionary.
        
        Returns:
            Dictionary with statistics
        """
        pass
    
    @abstractmethod
    def reset(self) -> None:
        """Reset all statistics."""
        pass


class Cache(ABC):
    """Interface for a cache."""
    
    @abstractmethod
    def get(self, key: Any) -> Optional[Any]:
        """
        Get an item from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        pass
    
    @abstractmethod
    def set(self, key: Any, value: Any) -> None:
        """
        Set an item in the cache.
        
        Args:
            key: Cache key
            value: Value to store
        """
        pass
    
    @abstractmethod
    def delete(self, key: Any) -> bool:
        """
        Delete an item from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Success indicator
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear the entire cache."""
        pass
    
    @abstractmethod
    def get_with_custom_ttl(self, key: Any, ttl: float) -> Optional[Any]:
        """
        Get an item with a custom TTL check.
        
        Args:
            key: Cache key
            ttl: Custom TTL to check against
            
        Returns:
            Cached value or None if not found or expired
        """
        pass
    
    @abstractmethod
    def add_invalidation_pattern(self, pattern: str, ttl: Optional[float] = None) -> None:
        """
        Add a pattern for invalidating cache entries.
        
        Args:
            pattern: Regex pattern string to match against keys
            ttl: Optional custom TTL for items matching this pattern
        """
        pass
    
    @abstractmethod
    def invalidate_by_pattern(self, pattern: str) -> int:
        """
        Invalidate all items matching a pattern.
        
        Args:
            pattern: Pattern to match against keys
            
        Returns:
            Number of invalidated items
        """
        pass
    
    @abstractmethod
    def get_lru_items(self, count: int = 5) -> List[Tuple[Any, Any]]:
        """
        Get the least recently used items.
        
        Args:
            count: Number of items to return
            
        Returns:
            List of (key, value) tuples of least recently used items
        """
        pass
    
    @abstractmethod
    def get_mru_items(self, count: int = 5) -> List[Tuple[Any, Any]]:
        """
        Get the most recently used items.
        
        Args:
            count: Number of items to return
            
        Returns:
            List of (key, value) tuples of most recently used items
        """
        pass
    
    @abstractmethod
    def get_statistics(self) -> CacheStatistics:
        """
        Get cache statistics.
        
        Returns:
            Cache statistics object
        """
        pass


class CacheManager(ABC):
    """Interface for a cache manager that handles multiple caches."""
    
    @abstractmethod
    def get_tickets_cache(self) -> Cache:
        """
        Get the tickets cache.
        
        Returns:
            Tickets cache
        """
        pass
    
    @abstractmethod
    def get_views_cache(self) -> Cache:
        """
        Get the views cache.
        
        Returns:
            Views cache
        """
        pass
    
    @abstractmethod
    def get_users_cache(self) -> Cache:
        """
        Get the users cache.
        
        Returns:
            Users cache
        """
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for all caches.
        
        Returns:
            Dictionary with cache statistics
        """
        pass
    
    @abstractmethod
    def clear_all(self) -> None:
        """Clear all caches."""
        pass
    
    @abstractmethod
    def reset_statistics(self) -> None:
        """Reset statistics for all caches."""
        pass
    
    @abstractmethod
    def set_custom_ttl(self, cache_type: str, ttl: int) -> bool:
        """
        Set a custom TTL for a specific cache type.
        
        Args:
            cache_type: Type of cache ('views', 'tickets', or 'users')
            ttl: New TTL in seconds
            
        Returns:
            Success indicator
        """
        pass
