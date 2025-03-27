"""
Cache Manager Module

This module provides caching functionality for Zendesk data
to reduce API calls and improve performance.
"""

import cachetools
import threading
import logging
from typing import Any, Dict, List, Optional
from datetime import timedelta

# Set up logging
logger = logging.getLogger(__name__)

class ZendeskCache:
    """
    Caching system for Zendesk data to improve performance and reduce API calls.
    Uses TTL (time-to-live) caches to ensure data freshness.
    """
    
    def __init__(self):
        """Initialize separate caches for different data types with appropriate TTLs."""
        # Cache for views data (15 minutes TTL)
        self._views_cache = cachetools.TTLCache(maxsize=100, ttl=900)  
        
        # Cache for tickets data (5 minutes TTL)
        self._tickets_cache = cachetools.TTLCache(maxsize=1000, ttl=300)  
        
        # Cache for user data (30 minutes TTL)
        self._user_cache = cachetools.TTLCache(maxsize=500, ttl=1800)
        
        # Thread lock for thread safety
        self._lock = threading.RLock()
        
    # Views cache methods
    
    def get_views(self, key: str) -> Optional[Any]:
        """Get a views cache entry."""
        with self._lock:
            value = self._views_cache.get(key)
            if value is not None:
                logger.debug(f"Cache hit for views cache: {key}")
            return value
            
    def set_views(self, key: str, value: Any) -> None:
        """Set a views cache entry."""
        with self._lock:
            self._views_cache[key] = value
            logger.debug(f"Stored in views cache: {key}")
    
    def invalidate_views(self) -> None:
        """Invalidate all views cache."""
        with self._lock:
            self._views_cache.clear()
            logger.debug("Invalidated views cache")
            
    # Tickets cache methods
    
    def get_tickets(self, key: str) -> Optional[Any]:
        """Get a tickets cache entry."""
        with self._lock:
            value = self._tickets_cache.get(key)
            if value is not None:
                logger.debug(f"Cache hit for tickets cache: {key}")
            return value
            
    def set_tickets(self, key: str, value: Any) -> None:
        """Set a tickets cache entry."""
        with self._lock:
            self._tickets_cache[key] = value
            logger.debug(f"Stored in tickets cache: {key}")
    
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
            
            for key in keys_to_remove:
                del self._tickets_cache[key]
                logger.debug(f"Invalidated cache entry for ticket {ticket_id}: {key}")
    
    def invalidate_tickets(self) -> None:
        """Invalidate all tickets cache."""
        with self._lock:
            self._tickets_cache.clear()
            logger.debug("Invalidated tickets cache")
            
    # User cache methods
    
    def get_user(self, key: str) -> Optional[Any]:
        """Get a user cache entry."""
        with self._lock:
            value = self._user_cache.get(key)
            if value is not None:
                logger.debug(f"Cache hit for user cache: {key}")
            return value
            
    def set_user(self, key: str, value: Any) -> None:
        """Set a user cache entry."""
        with self._lock:
            self._user_cache[key] = value
            logger.debug(f"Stored in user cache: {key}")
    
    def invalidate_user(self, user_id: str) -> None:
        """Invalidate cache entries for a specific user."""
        with self._lock:
            # Find and remove any keys containing this user ID
            keys_to_remove = [k for k in self._user_cache.keys() 
                             if str(user_id) in str(k)]
            
            for key in keys_to_remove:
                del self._user_cache[key]
                logger.debug(f"Invalidated cache entry for user {user_id}: {key}")
                
    def invalidate_users(self) -> None:
        """Invalidate all users cache."""
        with self._lock:
            self._user_cache.clear()
            logger.debug("Invalidated users cache")
            
    # Global cache management
            
    def clear_all(self) -> None:
        """Clear all caches."""
        with self._lock:
            self._views_cache.clear()
            self._tickets_cache.clear()
            self._user_cache.clear()
            logger.info("Cleared all caches")
            
    def get_stats(self) -> Dict[str, Dict[str, int]]:
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
                    "ttl": 900  # seconds
                },
                "tickets_cache": {
                    "size": len(self._tickets_cache),
                    "maxsize": self._tickets_cache.maxsize,
                    "ttl": 300  # seconds
                },
                "user_cache": {
                    "size": len(self._user_cache),
                    "maxsize": self._user_cache.maxsize,
                    "ttl": 1800  # seconds
                }
            }
            return stats
