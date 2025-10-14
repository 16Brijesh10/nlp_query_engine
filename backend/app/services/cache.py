# backend/app/services/cache.py

from typing import Dict, Any, Optional
import time
from datetime import datetime, timedelta

# Define the default cache expiration time
CACHE_TTL = timedelta(minutes=5)

class QueryCache:
    """
    Simple in-memory cache for storing query results.
    """
    def __init__(self):
        # Cache structure: {query_string: {"result": Any, "timestamp": datetime}}
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.hits = 0
        self.misses = 0

    def _is_valid(self, entry: Dict[str, Any]) -> bool:
        """Checks if a cache entry is still valid."""
        return datetime.now() < entry["timestamp"] + CACHE_TTL

    def get(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a result from the cache if it is valid.
        Returns the cached result dictionary (excluding timestamp) or None.
        """
        if query in self._cache:
            if self._is_valid(self._cache[query]):
                self.hits += 1
                # Return only the useful part of the result
                return self._cache[query]["result"]
            else:
                # Invalidate and remove expired entry
                del self._cache[query]
                self.misses += 1
                return None
        
        self.misses += 1
        return None

    def set(self, query: str, result: Dict[str, Any]):
        """
        Stores a new result in the cache.
        """
        self._cache[query] = {
            "result": result,
            "timestamp": datetime.now()
        }

    def clear(self):
        """Clears the entire cache. Required for schema/data updates."""
        self._cache = {}
        self.hits = 0
        self.misses = 0
        
    def get_stats(self) -> Dict[str, int | str]:
        """Returns current cache statistics."""
        total = self.hits + self.misses
        hit_rate = f"{self.hits / total * 100:.2f}%" if total > 0 else "0.00%"
        return {
            "entries": len(self._cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate
        }