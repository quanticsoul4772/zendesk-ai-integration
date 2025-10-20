"""
Zendesk Cache Adapter

This module provides a cache adapter for Zendesk data that implements the CacheManager interface.
"""

import logging
import time
from typing import Any, Dict, List, Optional, Tuple, cast

from src.domain.interfaces.cache_interfaces import Cache, CacheManager, CacheStatistics
from src.domain.entities.ticket import Ticket

# Set up logging
logger = logging.getLogger(__name__)


class ZendeskCacheStatistics(CacheStatistics):
    """Implementation of cache statistics for Zendesk caches."""

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
        self.last_access_time = time.time()
        self.total_access_time += access_time
        self.access_count += 1

    def get_hit_rate(self) -> float:
        """
        Get the cache hit rate.

        Returns:
            Float representing the hit rate (0-1)
        """
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0

    def get_average_access_time(self) -> float:
        """
        Get the average cache access time in milliseconds.

        Returns:
            Average access time in milliseconds
        """
        return (self.total_access_time / self.access_count) * 1000 if self.access_count > 0 else 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get all statistics as a dictionary.

        Returns:
            Dictionary with statistics
        """
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


class ZendeskCache(Cache):
    """Implementation of a cache for Zendesk data."""

    def __init__(self, maxsize: int = 1000, ttl: float = 300.0):
        """
        Initialize the cache.

        Args:
            maxsize: Maximum number of items in the cache
            ttl: Time-to-live in seconds
        """
        # Import cachetools here to avoid making it a direct dependency of the domain layer
        import cachetools
        import re
        import threading

        # Create TTL cache with additional attributes
        self._cache = cachetools.TTLCache(maxsize=maxsize, ttl=ttl)
        self._access_timestamps: Dict[Any, float] = {}
        self._update_timestamps: Dict[Any, float] = {}
        self._patterns: Dict[str, Dict[str, Any]] = {}

        # Thread lock for thread safety
        self._lock = threading.RLock()

        # Statistics
        self._statistics = ZendeskCacheStatistics()

    def get(self, key: Any) -> Optional[Any]:
        """
        Get an item from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or expired
        """
        with self._lock:
            start_time = time.time()

            try:
                if key not in self._cache:
                    self._statistics.record_miss(time.time() - start_time)
                    return None

                value = self._cache[key]
                self._access_timestamps[key] = time.time()

                # Check for empty value
                if value is None:
                    self._statistics.record_miss(time.time() - start_time)
                    return None

                # Check for empty collection
                if isinstance(value, (list, dict, set)) and len(value) == 0:
                    self._statistics.record_miss(time.time() - start_time)
                    return None

                self._statistics.record_hit(time.time() - start_time)
                return value
            except KeyError:
                self._statistics.record_miss(time.time() - start_time)
                return None

    def set(self, key: Any, value: Any) -> None:
        """
        Set an item in the cache.

        Args:
            key: Cache key
            value: Value to store
        """
        with self._lock:
            self._cache[key] = value
            current_time = time.time()
            self._access_timestamps[key] = current_time
            self._update_timestamps[key] = current_time

    def delete(self, key: Any) -> bool:
        """
        Delete an item from the cache.

        Args:
            key: Cache key

        Returns:
            Success indicator
        """
        with self._lock:
            try:
                del self._cache[key]
                self._access_timestamps.pop(key, None)
                self._update_timestamps.pop(key, None)
                return True
            except KeyError:
                return False

    def clear(self) -> None:
        """Clear the entire cache."""
        with self._lock:
            self._cache.clear()
            self._access_timestamps.clear()
            self._update_timestamps.clear()

    def get_with_custom_ttl(self, key: Any, ttl: float) -> Optional[Any]:
        """
        Get an item with a custom TTL check.

        Args:
            key: Cache key
            ttl: Custom TTL to check against

        Returns:
            Cached value or None if not found or expired
        """
        with self._lock:
            start_time = time.time()

            try:
                if key not in self._cache:
                    self._statistics.record_miss(time.time() - start_time)
                    return None

                # Get the current time and the time the item was last accessed
                current_time = time.time()
                timestamp = self._access_timestamps.get(key, 0)

                # Check if the item has expired according to the custom TTL
                if current_time - timestamp > ttl:
                    # Item has expired, remove it
                    del self._cache[key]
                    self._access_timestamps.pop(key, None)
                    self._update_timestamps.pop(key, None)
                    self._statistics.record_miss(time.time() - start_time)
                    return None

                # Item hasn't expired, return it and update access timestamp
                value = self._cache[key]
                self._access_timestamps[key] = current_time

                self._statistics.record_hit(time.time() - start_time)
                return value
            except KeyError:
                # Item might have been evicted or removed
                self._statistics.record_miss(time.time() - start_time)
                return None

    def add_invalidation_pattern(self, pattern: str, ttl: Optional[float] = None) -> None:
        """
        Add a pattern for invalidating cache entries.

        Args:
            pattern: Regex pattern string to match against keys
            ttl: Optional custom TTL for items matching this pattern
        """
        with self._lock:
            import re
            self._patterns[pattern] = {"pattern": re.compile(pattern), "ttl": ttl}

    def invalidate_by_pattern(self, pattern: str) -> int:
        """
        Invalidate all items matching a pattern.

        Args:
            pattern: Pattern to match against keys

        Returns:
            Number of invalidated items
        """
        with self._lock:
            import re
            try:
                pattern_re = re.compile(pattern)
                keys_to_remove = [k for k in self._cache if pattern_re.search(str(k))]

                for key in keys_to_remove:
                    del self._cache[key]
                    self._access_timestamps.pop(key, None)
                    self._update_timestamps.pop(key, None)

                return len(keys_to_remove)
            except re.error:
                logger.error(f"Invalid regex pattern: {pattern}")
                return 0

    def get_lru_items(self, count: int = 5) -> List[Tuple[Any, Any]]:
        """
        Get the least recently used items.

        Args:
            count: Number of items to return

        Returns:
            List of (key, value) tuples of least recently used items
        """
        with self._lock:
            sorted_keys = sorted(self._access_timestamps.keys(),
                                key=lambda k: self._access_timestamps[k])

            return [(k, self._cache[k]) for k in sorted_keys[:count] if k in self._cache]

    def get_mru_items(self, count: int = 5) -> List[Tuple[Any, Any]]:
        """
        Get the most recently used items.

        Args:
            count: Number of items to return

        Returns:
            List of (key, value) tuples of most recently used items
        """
        with self._lock:
            sorted_keys = sorted(self._access_timestamps.keys(),
                                key=lambda k: self._access_timestamps[k],
                                reverse=True)

            return [(k, self._cache[k]) for k in sorted_keys[:count] if k in self._cache]

    def get_statistics(self) -> CacheStatistics:
        """
        Get cache statistics.

        Returns:
            Cache statistics object
        """
        return self._statistics


class ZendeskCacheManager(CacheManager):
    """Implementation of a cache manager for Zendesk data."""

    def __init__(self):
        """Initialize the cache manager."""
        # Create caches for different data types with appropriate TTLs
        self._tickets_cache = ZendeskCache(maxsize=1000, ttl=300.0)  # 5 minutes
        self._views_cache = ZendeskCache(maxsize=100, ttl=900.0)  # 15 minutes
        self._users_cache = ZendeskCache(maxsize=500, ttl=1800.0)  # 30 minutes

        # Set up invalidation patterns
        self._tickets_cache.add_invalidation_pattern(r"tickets_.*", 300.0)
        self._tickets_cache.add_invalidation_pattern(r"view_tickets_.*", 300.0)
        self._views_cache.add_invalidation_pattern(r"all_views", 900.0)
        self._views_cache.add_invalidation_pattern(r"view_\d+", 900.0)

    def get_tickets_cache(self) -> Cache:
        """
        Get the tickets cache.

        Returns:
            Tickets cache
        """
        return self._tickets_cache

    def get_views_cache(self) -> Cache:
        """
        Get the views cache.

        Returns:
            Views cache
        """
        return self._views_cache

    def get_users_cache(self) -> Cache:
        """
        Get the users cache.

        Returns:
            Users cache
        """
        return self._users_cache

    def get_statistics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for all caches.

        Returns:
            Dictionary with cache statistics
        """
        return {
            "tickets_cache": {
                "statistics": self._tickets_cache.get_statistics().get_stats(),
                "size": len(self._tickets_cache._cache),
                "maxsize": self._tickets_cache._cache.maxsize,
                "ttl": self._tickets_cache._cache.ttl
            },
            "views_cache": {
                "statistics": self._views_cache.get_statistics().get_stats(),
                "size": len(self._views_cache._cache),
                "maxsize": self._views_cache._cache.maxsize,
                "ttl": self._views_cache._cache.ttl
            },
            "users_cache": {
                "statistics": self._users_cache.get_statistics().get_stats(),
                "size": len(self._users_cache._cache),
                "maxsize": self._users_cache._cache.maxsize,
                "ttl": self._users_cache._cache.ttl
            }
        }

    def clear_all(self) -> None:
        """Clear all caches."""
        self._tickets_cache.clear()
        self._views_cache.clear()
        self._users_cache.clear()

    def reset_statistics(self) -> None:
        """Reset statistics for all caches."""
        self._tickets_cache.get_statistics().reset()
        self._views_cache.get_statistics().reset()
        self._users_cache.get_statistics().reset()

    def set_custom_ttl(self, cache_type: str, ttl: int) -> bool:
        """
        Set a custom TTL for a specific cache type.

        Args:
            cache_type: Type of cache ('views', 'tickets', or 'users')
            ttl: New TTL in seconds

        Returns:
            Success indicator
        """
        if cache_type == "tickets":
            self._tickets_cache._cache.ttl = ttl
            return True
        elif cache_type == "views":
            self._views_cache._cache.ttl = ttl
            return True
        elif cache_type == "users":
            self._users_cache._cache.ttl = ttl
            return True
        else:
            return False

    # Additional helper methods specific to Zendesk data

    def get_ticket(self, key: str) -> Optional[Ticket]:
        """
        Get a ticket from the cache.

        Args:
            key: Cache key

        Returns:
            Ticket entity or None if not found
        """
        return cast(Optional[Ticket], self._tickets_cache.get(key))

    def set_ticket(self, key: str, ticket: Ticket) -> None:
        """
        Set a ticket in the cache.

        Args:
            key: Cache key
            ticket: Ticket entity
        """
        self._tickets_cache.set(key, ticket)

    def get_tickets(self, key: str) -> Optional[List[Ticket]]:
        """
        Get tickets from the cache.

        Args:
            key: Cache key

        Returns:
            List of ticket entities or None if not found
        """
        return cast(Optional[List[Ticket]], self._tickets_cache.get(key))

    def set_tickets(self, key: str, tickets: List[Ticket]) -> None:
        """
        Set tickets in the cache.

        Args:
            key: Cache key
            tickets: List of ticket entities
        """
        self._tickets_cache.set(key, tickets)

    def invalidate_ticket(self, ticket_id: str) -> None:
        """
        Invalidate cache entries for a specific ticket.

        Args:
            ticket_id: The ID of the ticket to invalidate
        """
        # Find and remove any keys containing this ticket ID
        self._tickets_cache.invalidate_by_pattern(f".*{ticket_id}.*")

    def get_views(self, key: str) -> Optional[Any]:
        """
        Get views from the cache.

        Args:
            key: Cache key

        Returns:
            View data or None if not found
        """
        return self._views_cache.get(key)

    def set_views(self, key: str, views: Any) -> None:
        """
        Set views in the cache.

        Args:
            key: Cache key
            views: View data
        """
        self._views_cache.set(key, views)

    def force_refresh_views(self) -> None:
        """Force refresh the views cache."""
        self._views_cache.clear()
