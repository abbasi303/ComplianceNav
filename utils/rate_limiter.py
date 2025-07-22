"""
Production-Grade Rate Limiting and Circuit Breaker
Protects APIs from overuse and provides graceful degradation
"""
import asyncio
import time
from typing import Dict, Any, Callable, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
import functools

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, failing fast
    HALF_OPEN = "half_open"  # Testing if service is back

@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_allowance: int = 10
    cooldown_seconds: int = 60

@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5
    recovery_timeout: int = 60
    half_open_max_calls: int = 3
    success_threshold: int = 2

class RateLimiter:
    """Token bucket rate limiter with burst support"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.tokens = config.burst_allowance
        self.last_refill = time.time()
        self.minute_requests = []
        self.hour_requests = []
    
    async def is_allowed(self, cost: int = 1) -> tuple[bool, Dict[str, Any]]:
        """Check if request is allowed"""
        now = time.time()
        
        # Clean old requests
        self._cleanup_old_requests(now)
        
        # Check rate limits
        if len(self.minute_requests) >= self.config.requests_per_minute:
            return False, {
                'reason': 'minute_limit_exceeded',
                'retry_after': 60 - (now - min(self.minute_requests)),
                'remaining_minute': 0
            }
        
        if len(self.hour_requests) >= self.config.requests_per_hour:
            return False, {
                'reason': 'hour_limit_exceeded', 
                'retry_after': 3600 - (now - min(self.hour_requests)),
                'remaining_hour': 0
            }
        
        # Check token bucket for burst protection
        self._refill_tokens(now)
        
        if self.tokens < cost:
            return False, {
                'reason': 'burst_limit_exceeded',
                'retry_after': self.config.cooldown_seconds,
                'tokens_available': self.tokens
            }
        
        # Allow request
        self.tokens -= cost
        self.minute_requests.append(now)
        self.hour_requests.append(now)
        
        return True, {
            'remaining_minute': self.config.requests_per_minute - len(self.minute_requests),
            'remaining_hour': self.config.requests_per_hour - len(self.hour_requests),
            'tokens_available': self.tokens
        }
    
    def _cleanup_old_requests(self, now: float):
        """Remove old request timestamps"""
        minute_ago = now - 60
        hour_ago = now - 3600
        
        self.minute_requests = [t for t in self.minute_requests if t > minute_ago]
        self.hour_requests = [t for t in self.hour_requests if t > hour_ago]
    
    def _refill_tokens(self, now: float):
        """Refill token bucket"""
        time_passed = now - self.last_refill
        tokens_to_add = int(time_passed * self.config.requests_per_minute / 60)
        
        self.tokens = min(
            self.config.burst_allowance,
            self.tokens + tokens_to_add
        )
        self.last_refill = now

class CircuitBreaker:
    """Circuit breaker for API protection"""
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.half_open_calls = 0
        
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        
        # Check if circuit is open
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                logger.info(f"Circuit breaker {self.name}: HALF_OPEN - attempting reset")
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker {self.name} is OPEN. "
                    f"Retry after {self._seconds_until_retry():.0f}s"
                )
        
        # Limit calls in half-open state
        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_calls >= self.config.half_open_max_calls:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker {self.name}: Too many HALF_OPEN calls"
                )
            self.half_open_calls += 1
        
        # Execute function
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            await self._on_success()
            return result
            
        except Exception as e:
            await self._on_failure(e)
            raise
    
    async def _on_success(self):
        """Handle successful call"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self._reset_circuit()
                logger.info(f"Circuit breaker {self.name}: CLOSED - recovered")
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0
    
    async def _on_failure(self, error: Exception):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        logger.warning(f"Circuit breaker {self.name}: Failure {self.failure_count}/{self.config.failure_threshold} - {error}")
        
        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN
            logger.error(f"Circuit breaker {self.name}: OPEN - too many failures")
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if not self.last_failure_time:
            return True
        return time.time() - self.last_failure_time >= self.config.recovery_timeout
    
    def _seconds_until_retry(self) -> float:
        """Calculate seconds until retry is allowed"""
        if not self.last_failure_time:
            return 0
        elapsed = time.time() - self.last_failure_time
        return max(0, self.config.recovery_timeout - elapsed)
    
    def _reset_circuit(self):
        """Reset circuit to closed state"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0

class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open"""
    pass

class ProductionAPIManager:
    """Production-ready API management with rate limiting and circuit breaking"""
    
    def __init__(self):
        self.rate_limiters = {}
        self.circuit_breakers = {}
        
        # Default configurations
        self.default_rate_config = RateLimitConfig(
            requests_per_minute=50,   # Conservative for production
            requests_per_hour=800,    # Daily limit consideration
            burst_allowance=8,        # Small burst allowance
            cooldown_seconds=30
        )
        
        self.default_circuit_config = CircuitBreakerConfig(
            failure_threshold=3,      # Fail fast
            recovery_timeout=45,      # Quick recovery attempts
            half_open_max_calls=2,    # Limited testing
            success_threshold=2       # Require multiple successes
        )
    
    def get_rate_limiter(self, service_name: str) -> RateLimiter:
        """Get or create rate limiter for service"""
        if service_name not in self.rate_limiters:
            config = self._get_rate_config(service_name)
            self.rate_limiters[service_name] = RateLimiter(config)
        return self.rate_limiters[service_name]
    
    def get_circuit_breaker(self, service_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for service"""
        if service_name not in self.circuit_breakers:
            config = self._get_circuit_config(service_name)
            self.circuit_breakers[service_name] = CircuitBreaker(service_name, config)
        return self.circuit_breakers[service_name]
    
    def _get_rate_config(self, service_name: str) -> RateLimitConfig:
        """Get service-specific rate limiting config"""
        service_configs = {
            'gemini_api': RateLimitConfig(
                requests_per_minute=30,  # Gemini has rate limits
                requests_per_hour=500,
                burst_allowance=5,
                cooldown_seconds=45
            ),
            'web_scraping': RateLimitConfig(
                requests_per_minute=20,  # Be respectful to websites
                requests_per_hour=400,
                burst_allowance=3,
                cooldown_seconds=60
            ),
            'vector_store': RateLimitConfig(
                requests_per_minute=100, # Local/fast operations
                requests_per_hour=2000,
                burst_allowance=20,
                cooldown_seconds=10
            )
        }
        return service_configs.get(service_name, self.default_rate_config)
    
    def _get_circuit_config(self, service_name: str) -> CircuitBreakerConfig:
        """Get service-specific circuit breaker config"""
        service_configs = {
            'gemini_api': CircuitBreakerConfig(
                failure_threshold=2,     # Fail fast for expensive API
                recovery_timeout=120,    # Longer recovery
                half_open_max_calls=1,   # Single test call
                success_threshold=1
            ),
            'web_scraping': CircuitBreakerConfig(
                failure_threshold=4,     # More tolerance for web errors
                recovery_timeout=60,
                half_open_max_calls=3,
                success_threshold=2
            )
        }
        return service_configs.get(service_name, self.default_circuit_config)
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all rate limiters and circuit breakers"""
        status = {
            'rate_limiters': {},
            'circuit_breakers': {}
        }
        
        for name, limiter in self.rate_limiters.items():
            status['rate_limiters'][name] = {
                'tokens_available': limiter.tokens,
                'minute_requests': len(limiter.minute_requests),
                'hour_requests': len(limiter.hour_requests)
            }
        
        for name, breaker in self.circuit_breakers.items():
            status['circuit_breakers'][name] = {
                'state': breaker.state.value,
                'failure_count': breaker.failure_count,
                'success_count': breaker.success_count,
                'seconds_until_retry': breaker._seconds_until_retry()
            }
        
        return status

# Decorator for easy rate limiting
def rate_limited(service_name: str):
    """Decorator to add rate limiting to functions"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            manager = api_manager
            rate_limiter = manager.get_rate_limiter(service_name)
            
            allowed, info = await rate_limiter.is_allowed()
            if not allowed:
                logger.warning(f"Rate limit exceeded for {service_name}: {info}")
                raise RateLimitExceededError(f"Rate limit exceeded: {info['reason']}")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Decorator for circuit breaker protection
def circuit_protected(service_name: str):
    """Decorator to add circuit breaker protection"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            manager = api_manager
            circuit_breaker = manager.get_circuit_breaker(service_name)
            
            return await circuit_breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator

class RateLimitExceededError(Exception):
    """Exception raised when rate limit is exceeded"""
    pass

# Global API manager instance
api_manager = ProductionAPIManager() 