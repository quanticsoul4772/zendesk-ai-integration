"""
Cache Manager Module

This module provides caching functionality for Zendesk data
to reduce API calls and improve performance.
"""

import cachetools
import threading
import logging
import time
import re
from typing import Any, Dict, List, Optional, Pattern, Tuple, Union
from datetime import datetime, timedelta

# Set up logging
logger = logging.getLogger(__name__)

class CacheStatistics:
    """Track cache performance statistics."""
    
    def __init__(self):
        """Initialize cache statistics."""
        self.hits = 0
        self.misses = 0
        self.last_access_time = None
        self.total_access_time = 0
        self.access_count = 0
    
    def record_hit(self, access_time: float = 0):
        """Record a cache hit."""
        self.hits += 1
        self.record_access(access_time)
    
    def record_miss(self, access_time: float = 0):
        """Record a cache miss."""
        self.misses += 1
        self.record_access(access_time)
    
    def record_access(self, access_time: float = 0):
        """Record a cache access."""
        self.last_access_time = datetime.now()
        self.total_access_time += access_time
        self.access_count += 1
    
    def get_hit_rate(self) -> float:
        """Get the cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0
    
    def get_average_access_time(self) -> float:
        """Get the average cache access time in milliseconds."""
        return (self.total_access_time / self.access_count) * 1000 if self.access_count > 0 else 0
    
    def get_stats(self) -> Dict[str, Union[int, float]]:
        """Get all statistics as a dictionary."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.get_hit_rate(),
            "average_access_time_ms": self.get_average_access_time(),
            "access_count": self.access_count
        }
    
    def reset(self):
        """Reset all statistics."""
        self.hits = 0
        self.misses = 0
        self.last_access_time = None
        self.total_access_time = 0
        self.access_count = 0


class TTLCacheWithInvalidation(cachetools.TTLCache):
    """Extended TTLCache with pattern-based invalidation capabilities."""
    
    def __init__(self, maxsize, ttl, **kwargs):
        """Initialize the cache with additional tracking."""
        super().__init__(maxsize, ttl, **kwargs)
        self.access_timestamps = {}  # Track when items were last accessed
        self.update_timestamps = {}  # Track when items were last updated
        self.patterns = {}  # Store invalidation patterns
    
    def __getitem__(self, key):
        """Get an item and update its access timestamp."""
        value = super().__getitem__(key)
        self.access_timestamps[key] = time.time()
        return value
    
    def __setitem__(self, key, value):
        """Set an item and record its timestamp."""
        super().__setitem__(key, value)
        current_time = time.time()
        self.access_timestamps[key] = current_time
        self.update_timestamps[key] = current_time
    
    def __delitem__(self, key):
        """Delete an item and its timestamp."""
        super().__delitem__(key)
        self.access_timestamps.pop(key, None)
        self.update_timestamps.pop(key, None)
    
    def add_invalidation_pattern(self, pattern_str: str, ttl: Optional[float] = None):
        """Add a pattern for invalidating cache entries.
        
        Args:
            pattern_str: Regex pattern string to match against keys
            ttl: Optional custom TTL for items matching this pattern
        """
        pattern = re.compile(pattern_str)
        self.patterns[pattern_str] = {"pattern": pattern, "ttl": ttl}
    
    def remove_invalidation_pattern(self, pattern_str: str):
        """Remove an invalidation pattern."""
        if pattern_str in self.patterns:
            del self.patterns[pattern_str]
    
    def invalidate_by_pattern(self, pattern_str: str) -> int:
        """Invalidate all items matching a pattern.
        
        Args:
            pattern_str: Pattern to match against keys
            
        Returns:
            Number of invalidated items
        """
        try:
            pattern = re.compile(pattern_str)
            keys_to_remove = [k for k in self if pattern.search(str(k))]
            for key in keys_to_remove:
                del self[key]
            return len(keys_to_remove)
        except re.error:
            logger.error(f"Invalid regex pattern: {pattern_str}")
            return 0
    
    def get_with_custom_ttl(self, key: Any, default_ttl: float = None) -> Optional[Any]:
        """Get an item with a custom TTL check.
        
        Args:
            key: Cache key
            default_ttl: Custom TTL to check against (overrides cache default)
            
        Returns:
            Cached value or None if expired
        """
        # First check if key exists
        try:
            if key not in self:
                return None
                
            # Get the current time and the time the item was last accessed
            current_time = time.time()
            timestamp = self.access_timestamps.get(key, 0)
            
            # Determine the TTL to use
            effective_ttl = self.ttl  # Default TTL
            
            # Check if any pattern applies a custom TTL
            for pattern_info in self.patterns.values():
                if pattern_info["ttl"] is not None and pattern_info["pattern"].search(str(key)):
                    effective_ttl = pattern_info["ttl"]
                    break
            
            # Override with provided TTL if specified
            if default_ttl is not None:
                effective_ttl = default_ttl
            
            # Check if the item has expired according to the effective TTL
            if current_time - timestamp > effective_ttl:
                # Item has expired, remove it
                self.pop(key, None)
                return None
            
            # Item hasn't expired, return it and update access timestamp
            value = self[key]
            self.access_timestamps[key] = current_time
            return value
        except KeyError:
            # Item might have been evicted or removed
            return None
    
    def get_lru_items(self, count: int = 5) -> List[Tuple[Any, Any]]:
        """Get the least recently used items.
        
        Args:
            count: Number of items to return
            
        Returns:
            List of (key, value) tuples of least recently used items
        """
        sorted_keys = sorted(self.access_timestamps.keys(), 
                            key=lambda k: self.access_timestamps[k])
        
        return [(k, self[k]) for k in sorted_keys[:count] if k in self]
    
    def get_mru_items(self, count: int = 5) -> List[Tuple[Any, Any]]:
        """Get the most recently used items.
        
        Args:
            count: Number of items to return
            
        Returns:
            List of (key, value) tuples of most recently used items
        """
        sorted_keys = sorted(self.access_timestamps.keys(), 
                            key=lambda k: self.access_timestamps[k],
                            reverse=True)
        
        return [(k, self[k]) for k in sorted_keys[:count] if k in self]


class ZendeskCache:
    """
    Caching system for Zendesk data to improve performance and reduce API calls.
    Uses TTL (time-to-live) caches to ensure data freshness.
    """
    
    def __init__(self, views_ttl: int = 900, tickets_ttl: int = 300, user_ttl: int = 1800):
        """Initialize separate caches for different data types with appropriate TTLs.
        
        Args:
            views_ttl: TTL for views cache in seconds (default: 15 minutes)
            tickets_ttl: TTL for tickets cache in seconds (default: 5 minutes)
            user_ttl: TTL for user cache in seconds (default: 30 minutes)
        """
        # Cache for views data
        self._views_cache = TTLCacheWithInvalidation(maxsize=100, ttl=views_ttl)  
        
        # Cache for tickets data
        self._tickets_cache = TTLCacheWithInvalidation(maxsize=1000, ttl=tickets_ttl)
        
        # Cache for user data
        self._user_cache = TTLCacheWithInvalidation(maxsize=500, ttl=user_ttl)
        
        # Thread lock for thread safety
        self._lock = threading.RLock()
        
        # Statistics tracking
        self._views_stats = CacheStatistics()
        self._tickets_stats = CacheStatistics()
        self._user_stats = CacheStatistics()
        
        # Default TTL values
        self._default_ttls = {
            "views": views_ttl,
            "tickets": tickets_ttl,
            "user": user_ttl
        }
        
    # Views cache methods
    
    def get_views(self, key: str, custom_ttl: Optional[float] = None) -> Optional[Any]:
        """Get a views cache entry.
        
        Args:
            key: Cache key
            custom_ttl: Optional custom TTL to check against
            
        Returns:
            Cached value or None if not found or expired
        """
        with self._lock:
            start_time = time.time()
            
            if custom_ttl is not None:
                value = self._views_cache.get_with_custom_ttl(key, custom_ttl)
            else:
                value = self._views_cache.get(key)
                
            access_time = time.time() - start_time
                
            if value is not None:
                # Check if value is empty collection
                if isinstance(value, (list, dict, set)) and len(value) == 0:
                    logger.warning(f"Cached value for {key} is empty, returning None to force refresh")
                    self._views_stats.record_miss(access_time)
                    return None
                    
                # For iterable objects like Zendesk API results, check if they're empty
                try:
                    if hasattr(value, '__iter__') and not isinstance(value, (str, dict)) and len(list(value)) == 0:
                        logger.warning(f"Cached iterable for {key} is empty, returning None to force refresh")
                        self._views_stats.record_miss(access_time)
                        return None
                except Exception as e:
                    logger.warning(f"Error checking cached value length: {e}, will use cache anyway")
                
                logger.debug(f"Cache hit for views cache: {key}")
                self._views_stats.record_hit(access_time)
            else:
                self._views_stats.record_miss(access_time)
                
            return value
            
    def set_views(self, key: str, value: Any) -> 'ZendeskCache':
        """Set a views cache entry.
        
        Args:
            key: Cache key
            value: Value to store
        """
        with self._lock:
            self._views_cache[key] = value
            logger.debug(f"Stored in views cache: {key}")
            return self
    
    def invalidate_views(self) -> 'ZendeskCache':
        """Invalidate all views cache."""
        with self._lock:
            self._views_cache.clear()
            logger.info("Invalidated views cache")
            return self
            
    def force_refresh_views(self) -> None:
        """Force refresh the views cache."""
        with self._lock:
            self._views_cache.clear()
            logger.info("Forced refresh of views cache")
    
    def add_views_invalidation_pattern(self, pattern: str, custom_ttl: Optional[float] = None) -> None:
        """Add a pattern for invalidating views cache entries.
        
        Args:
            pattern: Regex pattern string to match against keys
            custom_ttl: Optional custom TTL for items matching this pattern
        """
        with self._lock:
            self._views_cache.add_invalidation_pattern(pattern, custom_ttl)
            logger.debug(f"Added invalidation pattern '{pattern}' to views cache")
    
    def invalidate_views_by_pattern(self, pattern: str) -> int:
        """Invalidate views cache entries matching a pattern.
        
        Args:
            pattern: Pattern to match against keys
            
        Returns:
            Number of invalidated items
        """
        with self._lock:
            count = self._views_cache.invalidate_by_pattern(pattern)
            logger.debug(f"Invalidated {count} views cache entries with pattern '{pattern}'")
            return count
            
    # Tickets cache methods
    
    def get_tickets(self, key: str, custom_ttl: Optional[float] = None) -> Optional[Any]:
        """Get a tickets cache entry.
        
        Args:
            key: Cache key
            custom_ttl: Optional custom TTL to check against
            
        Returns:
            Cached value or None if not found or expired
        """
        with self._lock:
            start_time = time.time()
            
            if custom_ttl is not None:
                # More aggressive custom TTL handling
                try:
                    timestamp = self._tickets_cache.access_timestamps.get(key, 0)
                    if timestamp > 0 and time.time() - timestamp > custom_ttl:
                        # TTL expired, force delete
                        try:
                            del self._tickets_cache[key]
                            value = None
                        except KeyError:
                            value = None
                    else:
                        value = self._tickets_cache.get_with_custom_ttl(key, custom_ttl)
                except Exception as e:
                    logger.warning(f"Error in custom TTL check: {e}")
                    value = self._tickets_cache.get(key)
            else:
                value = self._tickets_cache.get(key)
                
            access_time = time.time() - start_time
                
            if value is not None:
                logger.debug(f"Cache hit for tickets cache: {key}")
                self._tickets_stats.record_hit(access_time)
            else:
                self._tickets_stats.record_miss(access_time)
                
            return value
            
    def set_tickets(self, key: str, value: Any) -> 'ZendeskCache':
        """Set a tickets cache entry.
        
        Args:
            key: Cache key
            value: Value to store
        """
        with self._lock:
            self._tickets_cache[key] = value
            logger.debug(f"Stored in tickets cache: {key}")
            return self
    
    def invalidate_ticket(self, ticket_id: str) -> None:
        """
        Invalidate cache entries for a specific ticket.
        
        Args:
            ticket_id: The ID of the ticket to invalidate
        """
        with self._lock:
            # Find and remove any keys containing this ticket ID
            keys_to_remove = [k for k in self._tickets_cache.keys() 
                             if str(ticket_id) in str(k)]
            
            # If no specific keys contain the ticket ID, invalidate all tickets
            if not keys_to_remove:
                logger.debug(f"No specific cache keys found for ticket {ticket_id}, invalidating all tickets")
                self.invalidate_tickets()
                return
                
            for key in keys_to_remove:
                del self._tickets_cache[key]
                logger.debug(f"Invalidated cache entry for ticket {ticket_id}: {key}")
    
    def invalidate_tickets(self) -> 'ZendeskCache':
        """Invalidate all tickets cache."""
        with self._lock:
            self._tickets_cache.clear()
            logger.debug("Invalidated tickets cache")
            return self
    
    def add_tickets_invalidation_pattern(self, pattern: str, custom_ttl: Optional[float] = None) -> None:
        """Add a pattern for invalidating tickets cache entries.
        
        Args:
            pattern: Regex pattern string to match against keys
            custom_ttl: Optional custom TTL for items matching this pattern
        """
        with self._lock:
            self._tickets_cache.add_invalidation_pattern(pattern, custom_ttl)
            logger.debug(f"Added invalidation pattern '{pattern}' to tickets cache")
    
    def invalidate_tickets_by_pattern(self, pattern: str) -> int:
        """Invalidate tickets cache entries matching a pattern.
        
        Args:
            pattern: Pattern to match against keys
            
        Returns:
            Number of invalidated items
        """
        with self._lock:
            count = self._tickets_cache.invalidate_by_pattern(pattern)
            logger.debug(f"Invalidated {count} tickets cache entries with pattern '{pattern}'")
            return count
            
    # User cache methods
    
    def get_user(self, key: str, custom_ttl: Optional[float] = None) -> Optional[Any]:
        """Get a user cache entry.
        
        Args:
            key: Cache key
            custom_ttl: Optional custom TTL to check against
            
        Returns:
            Cached value or None if not found or expired
        """
        with self._lock:
            start_time = time.time()
            
            if custom_ttl is not None:
                value = self._user_cache.get_with_custom_ttl(key, custom_ttl)
            else:
                value = self._user_cache.get(key)
                
            access_time = time.time() - start_time
                
            if value is not None:
                logger.debug(f"Cache hit for user cache: {key}")
                self._user_stats.record_hit(access_time)
            else:
                self._user_stats.record_miss(access_time)
                
            return value
            
    def set_user(self, key: str, value: Any) -> 'ZendeskCache':
        """Set a user cache entry.
        
        Args:
            key: Cache key
            value: Value to store
        """
        with self._lock:
            self._user_cache[key] = value
            logger.debug(f"Stored in user cache: {key}")
            return self
    
    def invalidate_user(self, user_id: str) -> None:
        """Invalidate cache entries for a specific user."""
        with self._lock:
            # Find and remove any keys containing this user ID
            keys_to_remove = [k for k in self._user_cache.keys() 
                             if str(user_id) in str(k)]
            
            for key in keys_to_remove:
                del self._user_cache[key]
                logger.debug(f"Invalidated cache entry for user {user_id}: {key}")
                
    def invalidate_users(self) -> 'ZendeskCache':
        """Invalidate all users cache."""
        with self._lock:
            self._user_cache.clear()
            logger.debug("Invalidated users cache")
            return self
    
    def add_user_invalidation_pattern(self, pattern: str, custom_ttl: Optional[float] = None) -> None:
        """Add a pattern for invalidating user cache entries.
        
        Args:
            pattern: Regex pattern string to match against keys
            custom_ttl: Optional custom TTL for items matching this pattern
        """
        with self._lock:
            self._user_cache.add_invalidation_pattern(pattern, custom_ttl)
            logger.debug(f"Added invalidation pattern '{pattern}' to user cache")
    
    def invalidate_user_by_pattern(self, pattern: str) -> int:
        """Invalidate user cache entries matching a pattern.
        
        Args:
            pattern: Pattern to match against keys
            
        Returns:
            Number of invalidated items
        """
        with self._lock:
            count = self._user_cache.invalidate_by_pattern(pattern)
            logger.debug(f"Invalidated {count} user cache entries with pattern '{pattern}'")
            return count
            
    # Custom TTL methods
    
    def set_custom_ttl(self, cache_type: str, ttl: int) -> bool:
        """
        Set a custom TTL for a specific cache type.
        
        Args:
            cache_type: Type of cache ('views', 'tickets', or 'user')
            ttl: New TTL in seconds
            
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            if cache_type not in self._default_ttls:
                logger.error(f"Invalid cache type: {cache_type}")
                return False
                
            # Update the default TTL
            self._default_ttls[cache_type] = ttl
            logger.info(f"Updated {cache_type} cache TTL to {ttl} seconds")
            
            # Create a new cache with the updated TTL
            if cache_type == "views":
                old_cache = self._views_cache
                self._views_cache = TTLCacheWithInvalidation(maxsize=old_cache.maxsize, ttl=ttl)
                # Copy over patterns
                for pattern_str, pattern_info in old_cache.patterns.items():
                    self._views_cache.add_invalidation_pattern(pattern_str, pattern_info["ttl"])
                # Copy over valid items
                for key, value in old_cache.items():
                    self._views_cache[key] = value
            elif cache_type == "tickets":
                old_cache = self._tickets_cache
                self._tickets_cache = TTLCacheWithInvalidation(maxsize=old_cache.maxsize, ttl=ttl)
                # Copy over patterns
                for pattern_str, pattern_info in old_cache.patterns.items():
                    self._tickets_cache.add_invalidation_pattern(pattern_str, pattern_info["ttl"])
                # Copy over valid items
                for key, value in old_cache.items():
                    self._tickets_cache[key] = value
            elif cache_type == "user":
                old_cache = self._user_cache
                self._user_cache = TTLCacheWithInvalidation(maxsize=old_cache.maxsize, ttl=ttl)
                # Copy over patterns
                for pattern_str, pattern_info in old_cache.patterns.items():
                    self._user_cache.add_invalidation_pattern(pattern_str, pattern_info["ttl"])
                # Copy over valid items
                for key, value in old_cache.items():
                    self._user_cache[key] = value
                    
            return True
    
    def set_custom_cache_size(self, cache_type: str, maxsize: int) -> bool:
        """
        Set a custom maximum size for a specific cache type.
        
        Args:
            cache_type: Type of cache ('views', 'tickets', or 'user')
            maxsize: New maximum size
            
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            if cache_type not in self._default_ttls:
                logger.error(f"Invalid cache type: {cache_type}")
                return False
                
            # Create a new cache with the updated size
            if cache_type == "views":
                old_cache = self._views_cache
                self._views_cache = TTLCacheWithInvalidation(maxsize=maxsize, ttl=old_cache.ttl)
                # Copy over patterns
                for pattern_str, pattern_info in old_cache.patterns.items():
                    self._views_cache.add_invalidation_pattern(pattern_str, pattern_info["ttl"])
                # Copy over valid items (may lose some if new size is smaller)
                for key, value in old_cache.items():
                    if len(self._views_cache) < maxsize:
                        self._views_cache[key] = value
            elif cache_type == "tickets":
                old_cache = self._tickets_cache
                self._tickets_cache = TTLCacheWithInvalidation(maxsize=maxsize, ttl=old_cache.ttl)
                # Copy over patterns
                for pattern_str, pattern_info in old_cache.patterns.items():
                    self._tickets_cache.add_invalidation_pattern(pattern_str, pattern_info["ttl"])
                # Copy over valid items (may lose some if new size is smaller)
                for key, value in old_cache.items():
                    if len(self._tickets_cache) < maxsize:
                        self._tickets_cache[key] = value
            elif cache_type == "user":
                old_cache = self._user_cache
                self._user_cache = TTLCacheWithInvalidation(maxsize=maxsize, ttl=old_cache.ttl)
                # Copy over patterns
                for pattern_str, pattern_info in old_cache.patterns.items():
                    self._user_cache.add_invalidation_pattern(pattern_str, pattern_info["ttl"])
                # Copy over valid items (may lose some if new size is smaller)
                for key, value in old_cache.items():
                    if len(self._user_cache) < maxsize:
                        self._user_cache[key] = value
                    
            logger.info(f"Updated {cache_type} cache size to {maxsize}")
            return True
            
    # Global cache management
            
    def clear_all(self) -> 'ZendeskCache':
        """Clear all caches."""
        with self._lock:
            self._views_cache.clear()
            self._tickets_cache.clear()
            self._user_cache.clear()
            logger.info("Cleared all caches")
            return self
    
    def reset_statistics(self) -> 'ZendeskCache':
        """Reset all cache statistics."""
        with self._lock:
            self._views_stats.reset()
            self._tickets_stats.reset()
            self._user_stats.reset()
            logger.info("Reset all cache statistics")
            return self
            
    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics about the current cache state.
        
        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            stats = {
                "views_cache": {
                    "size": len(self._views_cache),
                    "maxsize": self._views_cache.maxsize,
                    "ttl": self._default_ttls["views"],
                    "performance": self._views_stats.get_stats()
                },
                "tickets_cache": {
                    "size": len(self._tickets_cache),
                    "maxsize": self._tickets_cache.maxsize,
                    "ttl": self._default_ttls["tickets"],
                    "performance": self._tickets_stats.get_stats()
                },
                "user_cache": {
                    "size": len(self._user_cache),
                    "maxsize": self._user_cache.maxsize,
                    "ttl": self._default_ttls["user"],
                    "performance": self._user_stats.get_stats()
                }
            }
            return stats
    
    def get_lru_items(self, cache_type: str, count: int = 5) -> List[Tuple[Any, Any]]:
        """
        Get the least recently used items from a specific cache.
        
        Args:
            cache_type: Type of cache ('views', 'tickets', or 'user')
            count: Number of items to return
            
        Returns:
            List of (key, value) tuples of least recently used items
        """
        with self._lock:
            if cache_type == "views":
                return self._views_cache.get_lru_items(count)
            elif cache_type == "tickets":
                return self._tickets_cache.get_lru_items(count)
            elif cache_type == "user":
                return self._user_cache.get_lru_items(count)
            else:
                logger.error(f"Invalid cache type: {cache_type}")
                return []
    
    def get_mru_items(self, cache_type: str, count: int = 5) -> List[Tuple[Any, Any]]:
        """
        Get the most recently used items from a specific cache.
        
        Args:
            cache_type: Type of cache ('views', 'tickets', or 'user')
            count: Number of items to return
            
        Returns:
            List of (key, value) tuples of most recently used items
        """
        with self._lock:
            if cache_type == "views":
                return self._views_cache.get_mru_items(count)
            elif cache_type == "tickets":
                return self._tickets_cache.get_mru_items(count)
            elif cache_type == "user":
                return self._user_cache.get_mru_items(count)
            else:
                logger.error(f"Invalid cache type: {cache_type}")
                return []
