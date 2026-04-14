"""
Cache management utilities for the Tahqiq application.
Provides in-memory caching for frequently accessed data.
"""

import time
import threading
from typing import Any, Dict, Optional, Callable
from collections import OrderedDict
import logging

logger = logging.getLogger(__name__)

class CacheEntry:
    """Container for cached data with metadata"""
    
    def __init__(self, value: Any, ttl: Optional[float] = None):
        self.value = value
        self.created_at = time.time()
        self.expires_at = self.created_at + ttl if ttl else None
        self.access_count = 0
        self.last_accessed = self.created_at
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    def access(self) -> Any:
        """Access the cached value and update metadata"""
        self.access_count += 1
        self.last_accessed = time.time()
        return self.value

class LRUCache:
    """Thread-safe LRU (Least Recently Used) cache implementation"""
    
    def __init__(self, max_size: int = 100, default_ttl: Optional[float] = None):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            
            entry = self._cache[key]
            
            # Check if expired
            if entry.is_expired():
                del self._cache[key]
                self._misses += 1
                logger.debug(f"Cache entry expired: {key}")
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._hits += 1
            
            return entry.access()
    
    def put(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Put value into cache"""
        with self._lock:
            # Use provided TTL or default
            entry_ttl = ttl if ttl is not None else self.default_ttl
            entry = CacheEntry(value, entry_ttl)
            
            # If key exists, update it
            if key in self._cache:
                self._cache[key] = entry
                self._cache.move_to_end(key)
            else:
                # Add new entry
                self._cache[key] = entry
                
                # Remove oldest entries if over capacity
                while len(self._cache) > self.max_size:
                    oldest_key = next(iter(self._cache))
                    del self._cache[oldest_key]
                    logger.debug(f"Evicted from cache: {oldest_key}")
    
    def remove(self, key: str) -> bool:
        """Remove entry from cache"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            logger.info("Cache cleared")
    
    def size(self) -> int:
        """Get current cache size"""
        with self._lock:
            return len(self._cache)
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count removed"""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': hit_rate,
                'memory_usage': sum(1 for _ in self._cache)  # Approximate
            }

class CacheManager:
    """Global cache manager with multiple cache instances"""
    
    def __init__(self):
        self._caches: Dict[str, LRUCache] = {}
        self._default_size = 100
        self._default_ttl = 300  # 5 minutes
    
    def get_cache(self, name: str, max_size: Optional[int] = None, 
                  ttl: Optional[float] = None) -> LRUCache:
        """Get or create a cache instance"""
        if name not in self._caches:
            cache_size = max_size if max_size is not None else self._default_size
            cache_ttl = ttl if ttl is not None else self._default_ttl
            self._caches[name] = LRUCache(cache_size, cache_ttl)
            logger.info(f"Created cache '{name}' with size {cache_size}, TTL {cache_ttl}s")
        
        return self._caches[name]
    
    def get(self, cache_name: str, key: str) -> Optional[Any]:
        """Get value from specific cache"""
        cache = self.get_cache(cache_name)
        return cache.get(key)
    
    def put(self, cache_name: str, key: str, value: Any, 
              ttl: Optional[float] = None) -> None:
        """Put value into specific cache"""
        cache = self.get_cache(cache_name)
        cache.put(key, value, ttl)
    
    def remove(self, cache_name: str, key: str) -> bool:
        """Remove entry from specific cache"""
        if cache_name in self._caches:
            return self._caches[cache_name].remove(key)
        return False
    
    def clear(self, cache_name: Optional[str] = None) -> None:
        """Clear specific cache or all caches"""
        if cache_name:
            if cache_name in self._caches:
                self._caches[cache_name].clear()
        else:
            for cache in self._caches.values():
                cache.clear()
    
    def cleanup_expired(self) -> Dict[str, int]:
        """Clean up expired entries in all caches"""
        results = {}
        for name, cache in self._caches.items():
            results[name] = cache.cleanup_expired()
        return results
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all caches"""
        return {name: cache.get_stats() for name, cache in self._caches.items()}

def cached(cache_name: str, ttl: Optional[float] = None, 
          key_func: Optional[Callable] = None):
    """
    Decorator for caching function results
    
    Args:
        cache_name: Name of the cache to use
        ttl: Time to live for cached results
        key_func: Function to generate cache key from arguments
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            result = cache_manager.get(cache_name, cache_key)
            if result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.put(cache_name, cache_key, result, ttl)
            logger.debug(f"Cached result for {func.__name__}")
            
            return result
        
        return wrapper
    return decorator

# Global cache manager instance
cache_manager = CacheManager()

# Predefined caches
AUTHORS_CACHE = "authors"
BOOKS_CACHE = "books"
MANUSCRIPTS_CACHE = "manuscripts"
RELATIONS_CACHE = "relations"

def initialize_caches():
    """Initialize commonly used caches with appropriate settings"""
    # Authors cache - larger size, longer TTL
    cache_manager.get_cache(AUTHORS_CACHE, max_size=500, ttl=600)  # 10 minutes
    
    # Books cache - medium size, medium TTL
    cache_manager.get_cache(BOOKS_CACHE, max_size=200, ttl=300)  # 5 minutes
    
    # Manuscripts cache - smaller size, shorter TTL
    cache_manager.get_cache(MANUSCRIPTS_CACHE, max_size=100, ttl=180)  # 3 minutes
    
    # Relations cache - medium size, short TTL
    cache_manager.get_cache(RELATIONS_CACHE, max_size=150, ttl=120)  # 2 minutes
    
    logger.info("Cache system initialized")
