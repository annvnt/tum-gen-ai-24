"""
Rate limiting utilities for financial platform
Provides IP-based and user-based rate limiting
"""

import time
import redis
from typing import Dict, Optional, Any
import logging
from functools import wraps
from fastapi import Request, HTTPException, status

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiting with Redis backend"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", db: int = 1):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True, db=db)
            self.redis_client.ping()
            logger.info("Redis rate limiter initialized")
        except redis.ConnectionError:
            logger.warning("Redis connection failed, using in-memory fallback")
            self.redis_client = None
            self._memory_store = {}
    
    def check_rate_limit(self, key: str, limit: int, window: int = 60) -> bool:
        """Check if request is within rate limit"""
        current_time = int(time.time())
        
        if self.redis_client:
            try:
                pipeline = self.redis_client.pipeline()
                pipeline.zadd(key, {str(current_time): current_time})
                pipeline.zremrangebyscore(key, 0, current_time - window)
                pipeline.zcard(key)
                pipeline.expire(key, window)
                
                results = pipeline.execute()
                request_count = results[2]
                
                return request_count <= limit
                
            except redis.RedisError as e:
                logger.error(f"Redis error checking rate limit: {e}")
                return self._check_memory_rate_limit(key, limit, window)
        else:
            return self._check_memory_rate_limit(key, limit, window)
    
    def get_rate_limit_info(self, key: str) -> Dict[str, Any]:
        """Get current rate limit information"""
        current_time = int(time.time())
        
        if self.redis_client:
            try:
                count = self.redis_client.zcard(key)
                oldest = self.redis_client.zrange(key, 0, 0, withscores=True)
                
                return {
                    "count": count,
                    "oldest_request": oldest[0][1] if oldest else None,
                    "window_remaining": max(0, 60 - (current_time - (oldest[0][1] if oldest else current_time)))
                }
            except redis.RedisError:
                return self._get_memory_rate_limit_info(key)
        else:
            return self._get_memory_rate_limit_info(key)
    
    def _check_memory_rate_limit(self, key: str, limit: int, window: int) -> bool:
        """Check rate limit using in-memory store"""
        current_time = int(time.time())
        
        if key not in self._memory_store:
            self._memory_store[key] = []
        
        # Clean old requests
        self._memory_store[key] = [
            timestamp for timestamp in self._memory_store[key]
            if current_time - timestamp < window
        ]
        
        # Add current request
        self._memory_store[key].append(current_time)
        
        return len(self._memory_store[key]) <= limit
    
    def _get_memory_rate_limit_info(self, key: str) -> Dict[str, Any]:
        """Get rate limit info from memory store"""
        if key not in self._memory_store:
            return {"count": 0, "oldest_request": None, "window_remaining": 60}
        
        current_time = int(time.time())
        timestamps = self._memory_store[key]
        
        if not timestamps:
            return {"count": 0, "oldest_request": None, "window_remaining": 60}
        
        oldest = min(timestamps)
        return {
            "count": len(timestamps),
            "oldest_request": oldest,
            "window_remaining": max(0, 60 - (current_time - oldest))
        }
    
    def get_client_ip(self, request: Request) -> str:
        """Get client IP from request"""
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def rate_limit(self, requests: int = 100, window: int = 60, key_func=None):
        """Rate limiting decorator for FastAPI endpoints"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                request = None
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
                
                if not request:
                    for kwarg in kwargs.values():
                        if isinstance(kwarg, Request):
                            request = kwarg
                            break
                
                if not request:
                    return await func(*args, **kwargs)
                
                # Generate rate limit key
                if key_func:
                    key = key_func(request)
                else:
                    key = f"rate_limit:{self.get_client_ip(request)}:{func.__name__}"
                
                if not self.check_rate_limit(key, requests, window):
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Rate limit exceeded. Try again in {window} seconds."
                    )
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    
    def rate_limit_by_user(self, requests: int = 50, window: int = 60):
        """Rate limit by user ID"""
        def key_func(request):
            from ..security.auth_manager import auth_manager
            
            # This would need to extract user from token
            # For now, use IP as fallback
            return f"rate_limit:user:{self.get_client_ip(request)}:{request.url.path}"
        
        return self.rate_limit(requests, window, key_func)
    
    def rate_limit_by_ip(self, requests: int = 100, window: int = 60):
        """Rate limit by IP address"""
        def key_func(request):
            return f"rate_limit:ip:{self.get_client_ip(request)}"
        
        return self.rate_limit(requests, window, key_func)
    
    def rate_limit_uploads(self, requests: int = 10, window: int = 3600):
        """Rate limit file uploads"""
        def key_func(request):
            return f"rate_limit:upload:{self.get_client_ip(request)}"
        
        return self.rate_limit(requests, window, key_func)
    
    def cleanup_expired_limits(self) -> int:
        """Clean up expired rate limit entries"""
        cleaned_count = 0
        
        try:
            if self.redis_client:
                # Redis handles expiration automatically for sorted sets
                return 0
            else:
                # Clean memory store
                current_time = int(time.time())
                to_remove = []
                
                for key, timestamps in self._memory_store.items():
                    self._memory_store[key] = [
                        ts for ts in timestamps
                        if current_time - ts < 3600  # Keep 1 hour max
                    ]
                    
                    if not self._memory_store[key]:
                        to_remove.append(key)
                
                for key in to_remove:
                    del self._memory_store[key]
                    cleaned_count += 1
        
        except Exception as e:
            logger.error(f"Error cleaning up rate limits: {e}")
        
        return cleaned_count
    
    def get_rate_limit_stats(self) -> Dict[str, Any]:
        """Get rate limiting statistics"""
        stats = {
            "active_limits": 0,
            "redis_connected": bool(self.redis_client),
            "memory_fallback": not bool(self.redis_client)
        }
        
        try:
            if self.redis_client:
                stats["active_limits"] = len([
                    key for key in self.redis_client.scan_iter(match="rate_limit:*", count=1000)
                ])
            else:
                stats["active_limits"] = len(self._memory_store)
        except redis.RedisError:
            pass
        
        return stats


# Global rate limiter instance
rate_limiter = RateLimiter()


# Convenience decorators
rate_limit = rate_limiter.rate_limit
rate_limit_by_ip = rate_limiter.rate_limit_by_ip
rate_limit_by_user = rate_limiter.rate_limit_by_user
rate_limit_uploads = rate_limiter.rate_limit_uploads