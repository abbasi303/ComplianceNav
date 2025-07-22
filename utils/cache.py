"""
High-Performance Caching Layer for ComplianceNavigator
Reduces API calls and improves response times
"""
import hashlib
import json
import time
from typing import Any, Dict, List, Optional
from pathlib import Path
from loguru import logger
import pickle

class PerformanceCache:
    """High-performance cache for regulation searches and API responses"""
    
    def __init__(self, cache_dir: str = "data/cache", ttl: int = 3600):
        """
        Initialize performance cache
        
        Args:
            cache_dir: Directory to store cache files
            ttl: Time-to-live in seconds (default 1 hour)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl
        self.memory_cache = {}  # In-memory cache for frequently accessed items
        
        logger.info(f"Performance cache initialized with TTL {ttl}s")
    
    def _get_cache_key(self, key_data: Dict) -> str:
        """Generate unique cache key from data"""
        # Sort keys for consistent hashing
        sorted_data = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(sorted_data.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get file path for cache key"""
        return self.cache_dir / f"{cache_key}.cache"
    
    def _is_expired(self, timestamp: float) -> bool:
        """Check if cache entry is expired"""
        return (time.time() - timestamp) > self.ttl
    
    async def get_regulation_search(
        self, 
        country: str, 
        industry: str, 
        business_activities: List[str]
    ) -> Optional[List[Dict]]:
        """Get cached regulation search results"""
        cache_key_data = {
            'type': 'regulation_search',
            'country': country.lower(),
            'industry': industry.lower(),
            'activities': sorted([a.lower() for a in business_activities])
        }
        
        cache_key = self._get_cache_key(cache_key_data)
        
        # Check memory cache first
        if cache_key in self.memory_cache:
            data, timestamp = self.memory_cache[cache_key]
            if not self._is_expired(timestamp):
                logger.debug(f"Memory cache hit for regulation search: {country}")
                return data
            else:
                del self.memory_cache[cache_key]
        
        # Check file cache
        cache_path = self._get_cache_path(cache_key)
        if cache_path.exists():
            try:
                with open(cache_path, 'rb') as f:
                    cached_data = pickle.load(f)
                
                if not self._is_expired(cached_data['timestamp']):
                    # Load into memory cache for faster access
                    self.memory_cache[cache_key] = (cached_data['data'], cached_data['timestamp'])
                    logger.debug(f"File cache hit for regulation search: {country}")
                    return cached_data['data']
                else:
                    # Remove expired cache
                    cache_path.unlink()
                    logger.debug(f"Expired cache removed for: {country}")
                    
            except Exception as e:
                logger.error(f"Error reading cache: {e}")
        
        logger.debug(f"Cache miss for regulation search: {country}")
        return None
    
    async def set_regulation_search(
        self, 
        country: str, 
        industry: str, 
        business_activities: List[str],
        data: List[Dict]
    ) -> None:
        """Cache regulation search results"""
        cache_key_data = {
            'type': 'regulation_search',
            'country': country.lower(),
            'industry': industry.lower(),
            'activities': sorted([a.lower() for a in business_activities])
        }
        
        cache_key = self._get_cache_key(cache_key_data)
        timestamp = time.time()
        
        # Store in memory cache
        self.memory_cache[cache_key] = (data, timestamp)
        
        # Store in file cache
        cache_path = self._get_cache_path(cache_key)
        try:
            cached_data = {
                'data': data,
                'timestamp': timestamp,
                'metadata': {
                    'country': country,
                    'industry': industry,
                    'activities': business_activities
                }
            }
            
            with open(cache_path, 'wb') as f:
                pickle.dump(cached_data, f)
            
            logger.debug(f"Cached regulation search for: {country}")
            
        except Exception as e:
            logger.error(f"Error writing cache: {e}")
    
    async def get_api_response(self, prompt_hash: str) -> Optional[str]:
        """Get cached API response"""
        cache_key_data = {
            'type': 'api_response',
            'prompt_hash': prompt_hash
        }
        
        cache_key = self._get_cache_key(cache_key_data)
        
        # Check memory cache first
        if cache_key in self.memory_cache:
            data, timestamp = self.memory_cache[cache_key]
            if not self._is_expired(timestamp):
                logger.debug(f"Memory cache hit for API response")
                return data
            else:
                del self.memory_cache[cache_key]
        
        # Check file cache
        cache_path = self._get_cache_path(cache_key)
        if cache_path.exists():
            try:
                with open(cache_path, 'rb') as f:
                    cached_data = pickle.load(f)
                
                if not self._is_expired(cached_data['timestamp']):
                    self.memory_cache[cache_key] = (cached_data['data'], cached_data['timestamp'])
                    logger.debug(f"File cache hit for API response")
                    return cached_data['data']
                else:
                    cache_path.unlink()
                    
            except Exception as e:
                logger.error(f"Error reading API cache: {e}")
        
        return None
    
    async def set_api_response(self, prompt_hash: str, response: str) -> None:
        """Cache API response"""
        cache_key_data = {
            'type': 'api_response',
            'prompt_hash': prompt_hash
        }
        
        cache_key = self._get_cache_key(cache_key_data)
        timestamp = time.time()
        
        # Store in memory cache
        self.memory_cache[cache_key] = (response, timestamp)
        
        # Store in file cache
        cache_path = self._get_cache_path(cache_key)
        try:
            cached_data = {
                'data': response,
                'timestamp': timestamp
            }
            
            with open(cache_path, 'wb') as f:
                pickle.dump(cached_data, f)
            
            logger.debug(f"Cached API response")
            
        except Exception as e:
            logger.error(f"Error writing API cache: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        cache_files = list(self.cache_dir.glob("*.cache"))
        
        return {
            'memory_cache_size': len(self.memory_cache),
            'file_cache_size': len(cache_files),
            'cache_dir': str(self.cache_dir),
            'ttl_seconds': self.ttl
        }
    
    def clear_expired_cache(self) -> int:
        """Clear expired cache entries"""
        cleared_count = 0
        current_time = time.time()
        
        # Clear memory cache
        expired_keys = [
            k for k, (_, timestamp) in self.memory_cache.items() 
            if self._is_expired(timestamp)
        ]
        for key in expired_keys:
            del self.memory_cache[key]
            cleared_count += 1
        
        # Clear file cache
        cache_files = list(self.cache_dir.glob("*.cache"))
        for cache_path in cache_files:
            try:
                with open(cache_path, 'rb') as f:
                    cached_data = pickle.load(f)
                
                if self._is_expired(cached_data['timestamp']):
                    cache_path.unlink()
                    cleared_count += 1
                    
            except Exception as e:
                logger.error(f"Error checking cache file {cache_path}: {e}")
        
        if cleared_count > 0:
            logger.info(f"Cleared {cleared_count} expired cache entries")
        
        return cleared_count

# Global cache instance
performance_cache = PerformanceCache() 