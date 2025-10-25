"""
Redis Cache Service for High-Performance Caching and Session Management
Handles caching strategies, session storage, and cache invalidation
"""
import json
import logging
import pickle
from typing import Any, Dict, List, Optional, Union
import redis
from redis.exceptions import RedisError
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger(__name__)

class RedisService:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """
        Initialize Redis service
        
        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.client = None
        self.logger = logger
    
    @property
    def redis_client(self):
        """Property for backward compatibility with tests"""
        return self.client
        
    def initialize(self):
        """Initialize Redis client with connection pooling"""
        try:
            # Parse Redis URL
            if self.redis_url.startswith("redis://"):
                # Extract host and port from URL
                url_parts = self.redis_url.replace("redis://", "").split(":")
                host = url_parts[0]
                port = int(url_parts[1]) if len(url_parts) > 1 else 6379
                
                self.client = redis.Redis(
                    host=host,
                    port=port,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
            else:
                self.client = redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
            
            # Test connection
            self.client.ping()
            
            self.logger.info("Redis service initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Redis service: {str(e)}")
            raise
    
    def set_cache(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        serialize: bool = True
    ) -> bool:
        """
        Set cache value with optional TTL
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            serialize: Whether to serialize the value
            
        Returns:
            True if successful
        """
        try:
            if serialize:
                # Serialize complex objects
                if isinstance(value, (dict, list)):
                    serialized_value = json.dumps(value)
                else:
                    serialized_value = str(value)
            else:
                serialized_value = value
            
            if ttl:
                result = self.client.setex(key, ttl, serialized_value)
            else:
                result = self.client.set(key, serialized_value)
            
            return result
            
        except RedisError as e:
            self.logger.error(f"Failed to set cache for key '{key}': {str(e)}")
            return False
    
    def get_cache(
        self, 
        key: str, 
        deserialize: bool = True
    ) -> Optional[Any]:
        """
        Get cache value
        
        Args:
            key: Cache key
            deserialize: Whether to deserialize the value
            
        Returns:
            Cached value or None
        """
        try:
            value = self.client.get(key)
            
            if value is None:
                return None
            
            if deserialize:
                try:
                    # Try to deserialize JSON
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    # Return as string if not JSON
                    return value
            else:
                return value
                
        except RedisError as e:
            self.logger.error(f"Failed to get cache for key '{key}': {str(e)}")
            return None
    
    def delete_cache(self, key: str) -> bool:
        """
        Delete cache key
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if successful
        """
        try:
            result = self.client.delete(key)
            return result > 0
            
        except RedisError as e:
            self.logger.error(f"Failed to delete cache key '{key}': {str(e)}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern
        
        Args:
            pattern: Key pattern (e.g., "user:*")
            
        Returns:
            Number of keys deleted
        """
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
            
        except RedisError as e:
            self.logger.error(f"Failed to delete pattern '{pattern}': {str(e)}")
            return 0
    
    def set_session(
        self, 
        session_id: str, 
        session_data: Dict[str, Any], 
        ttl: int = 3600
    ) -> bool:
        """
        Set user session data
        
        Args:
            session_id: Session identifier
            session_data: Session data dictionary
            ttl: Session TTL in seconds (default: 1 hour)
            
        Returns:
            True if successful
        """
        try:
            session_key = f"session:{session_id}"
            session_data["last_activity"] = datetime.utcnow().isoformat()
            session_data["expires_at"] = (datetime.utcnow() + timedelta(seconds=ttl)).isoformat()
            
            return self.set_cache(session_key, session_data, ttl)
            
        except Exception as e:
            self.logger.error(f"Failed to set session '{session_id}': {str(e)}")
            return False
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user session data
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data or None
        """
        try:
            session_key = f"session:{session_id}"
            session_data = self.get_cache(session_key)
            
            if session_data and "expires_at" in session_data:
                expires_at = datetime.fromisoformat(session_data["expires_at"])
                if datetime.utcnow() > expires_at:
                    # Session expired
                    self.delete_cache(session_key)
                    return None
            
            return session_data
            
        except Exception as e:
            self.logger.error(f"Failed to get session '{session_id}': {str(e)}")
            return None
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete user session
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful
        """
        try:
            session_key = f"session:{session_id}"
            return self.delete_cache(session_key)
            
        except Exception as e:
            self.logger.error(f"Failed to delete session '{session_id}': {str(e)}")
            return False
    
    def cache_query_result(
        self, 
        query_hash: str, 
        result: Any, 
        ttl: int = 300
    ) -> bool:
        """
        Cache query result
        
        Args:
            query_hash: Hash of the query
            result: Query result
            ttl: Cache TTL in seconds
            
        Returns:
            True if successful
        """
        try:
            cache_key = f"query:{query_hash}"
            return self.set_cache(cache_key, result, ttl)
            
        except Exception as e:
            self.logger.error(f"Failed to cache query result: {str(e)}")
            return False
    
    def get_cached_query_result(self, query_hash: str) -> Optional[Any]:
        """
        Get cached query result
        
        Args:
            query_hash: Hash of the query
            
        Returns:
            Cached result or None
        """
        try:
            cache_key = f"query:{query_hash}"
            return self.get_cache(cache_key)
            
        except Exception as e:
            self.logger.error(f"Failed to get cached query result: {str(e)}")
            return None
    
    def cache_schema_data(
        self, 
        connection_hash: str, 
        schema_data: Dict[str, Any], 
        ttl: int = 3600
    ) -> bool:
        """
        Cache schema discovery data
        
        Args:
            connection_hash: Hash of the connection string
            schema_data: Schema data
            ttl: Cache TTL in seconds
            
        Returns:
            True if successful
        """
        try:
            cache_key = f"schema:{connection_hash}"
            return self.set_cache(cache_key, schema_data, ttl)
            
        except Exception as e:
            self.logger.error(f"Failed to cache schema data: {str(e)}")
            return False
    
    def get_cached_schema_data(self, connection_hash: str) -> Optional[Dict[str, Any]]:
        """
        Get cached schema data
        
        Args:
            connection_hash: Hash of the connection string
            
        Returns:
            Cached schema data or None
        """
        try:
            cache_key = f"schema:{connection_hash}"
            return self.get_cache(cache_key)
            
        except Exception as e:
            self.logger.error(f"Failed to get cached schema data: {str(e)}")
            return None
    
    def generate_cache_key(self, prefix: str, *args) -> str:
        """
        Generate cache key from prefix and arguments
        
        Args:
            prefix: Key prefix
            *args: Arguments to include in key
            
        Returns:
            Generated cache key
        """
        key_string = f"{prefix}:{':'.join(str(arg) for arg in args)}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform Redis health check
        
        Returns:
            Health check results
        """
        try:
            # Test basic connectivity
            start_time = datetime.utcnow()
            self.client.ping()
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Get Redis info
            info = self.client.info()
            
            return {
                "status": "healthy",
                "response_time": response_time,
                "redis_version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Redis health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Cache statistics
        """
        try:
            info = self.client.info()
            
            return {
                "total_keys": self.client.dbsize(),
                "used_memory": info.get("used_memory_human"),
                "hit_rate": info.get("keyspace_hits", 0) / max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1),
                "connected_clients": info.get("connected_clients"),
                "uptime": info.get("uptime_in_seconds")
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get cache stats: {str(e)}")
            return {}

# Global Redis service instance
redis_service: Optional[RedisService] = None

def get_redis_service() -> RedisService:
    """Get the global Redis service instance"""
    if redis_service is None:
        raise RuntimeError("Redis service not initialized")
    return redis_service

def initialize_redis_service(redis_url: str) -> RedisService:
    """Initialize the global Redis service"""
    global redis_service
    redis_service = RedisService(redis_url)
    redis_service.initialize()
    return redis_service
