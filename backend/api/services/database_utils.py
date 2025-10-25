"""
Database Utility Functions
Common database operations, validation, and helper functions
"""
import logging
import hashlib
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from .database_manager import get_database_manager
from .redis_service import get_redis_service
from .chromadb_service import get_chromadb_service
from ..models.database_models import (
    QueryHistory, DocumentMetadata, SchemaCache, 
    PerformanceMetrics, UserSession, SystemLog, DatabaseConnection
)

logger = logging.getLogger(__name__)

class DatabaseUtils:
    """Utility functions for common database operations"""
    
    def __init__(self):
        self.logger = logger
        self.redis_service = get_redis_service()
        self.chromadb_service = get_chromadb_service()
    
    def generate_query_hash(self, query_text: str, query_type: str) -> str:
        """
        Generate a hash for query caching
        
        Args:
            query_text: Query text
            query_type: Type of query (sql, document, hybrid)
            
        Returns:
            Query hash string
        """
        query_string = f"{query_type}:{query_text}"
        return hashlib.md5(query_string.encode()).hexdigest()
    
    def generate_connection_hash(self, connection_string: str) -> str:
        """
        Generate a hash for connection string caching
        
        Args:
            connection_string: Database connection string
            
        Returns:
            Connection hash string
        """
        return hashlib.sha256(connection_string.encode()).hexdigest()
    
    def log_query(
        self, 
        session: Session,
        query_text: str,
        query_type: str,
        response_time: float,
        cache_hit: bool = False,
        user_session_id: Optional[str] = None,
        sql_generated: Optional[str] = None,
        entities_extracted: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log a query to the database
        
        Args:
            session: Database session
            query_text: Query text
            query_type: Type of query
            response_time: Response time in seconds
            cache_hit: Whether the result was cached
            user_session_id: User session ID
            sql_generated: Generated SQL (if applicable)
            entities_extracted: Extracted entities
            
        Returns:
            Query ID
        """
        try:
            query = QueryHistory(
                query_text=query_text,
                query_type=query_type,
                response_time=response_time,
                cache_hit=cache_hit,
                user_session_id=user_session_id,
                sql_generated=sql_generated,
                entities_extracted=entities_extracted
            )
            
            session.add(query)
            session.commit()
            session.refresh(query)
            
            self.logger.info(f"Logged query: {query.id}")
            return str(query.id)
            
        except Exception as e:
            self.logger.error(f"Failed to log query: {str(e)}")
            session.rollback()
            raise
    
    def log_performance_metric(
        self,
        session: Session,
        query_id: str,
        metric_name: str,
        metric_value: float,
        metric_unit: Optional[str] = None
    ) -> str:
        """
        Log a performance metric
        
        Args:
            session: Database session
            query_id: Query ID
            metric_name: Metric name
            metric_value: Metric value
            metric_unit: Metric unit
            
        Returns:
            Metric ID
        """
        try:
            metric = PerformanceMetrics(
                query_id=query_id,
                metric_name=metric_name,
                metric_value=metric_value,
                metric_unit=metric_unit
            )
            
            session.add(metric)
            session.commit()
            session.refresh(metric)
            
            return str(metric.id)
            
        except Exception as e:
            self.logger.error(f"Failed to log performance metric: {str(e)}")
            session.rollback()
            raise
    
    def create_user_session(
        self,
        session: Session,
        session_token: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        ttl_hours: int = 24
    ) -> str:
        """
        Create a user session
        
        Args:
            session: Database session
            session_token: Session token
            user_id: User ID
            ip_address: IP address
            user_agent: User agent string
            ttl_hours: Time to live in hours
            
        Returns:
            Session ID
        """
        try:
            expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
            
            user_session = UserSession(
                session_token=session_token,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                expires_at=expires_at
            )
            
            session.add(user_session)
            session.commit()
            session.refresh(user_session)
            
            # Also cache in Redis
            session_data = {
                "user_id": user_id,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "created_at": datetime.utcnow().isoformat()
            }
            self.redis_service.set_session(
                session_token, 
                session_data, 
                ttl_hours * 3600
            )
            
            return str(user_session.id)
            
        except Exception as e:
            self.logger.error(f"Failed to create user session: {str(e)}")
            session.rollback()
            raise
    
    def validate_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a user session
        
        Args:
            session_token: Session token
            
        Returns:
            Session data if valid, None otherwise
        """
        try:
            # Check Redis cache first
            session_data = self.redis_service.get_session(session_token)
            if session_data:
                return session_data
            
            # Fallback to database
            db_manager = get_database_manager()
            with db_manager.get_session() as db_session:
                user_session = db_session.query(UserSession).filter(
                    UserSession.session_token == session_token,
                    UserSession.is_active == True,
                    UserSession.expires_at > datetime.utcnow()
                ).first()
                
                if user_session:
                    session_data = user_session.to_dict()
                    # Cache in Redis
                    self.redis_service.set_session(
                        session_token, 
                        session_data, 
                        3600  # 1 hour
                    )
                    return session_data
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to validate session: {str(e)}")
            return None
    
    def cache_schema_data(
        self,
        session: Session,
        connection_string: str,
        schema_data: Dict[str, Any],
        ttl_hours: int = 24
    ) -> str:
        """
        Cache schema data
        
        Args:
            session: Database session
            connection_string: Connection string
            schema_data: Schema data
            ttl_hours: Time to live in hours
            
        Returns:
            Cache ID
        """
        try:
            connection_hash = self.generate_connection_hash(connection_string)
            expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
            
            # Store in database
            schema_cache = SchemaCache(
                connection_string_hash=connection_hash,
                schema_data=schema_data,
                expires_at=expires_at
            )
            
            session.add(schema_cache)
            session.commit()
            session.refresh(schema_cache)
            
            # Also cache in Redis
            self.redis_service.cache_schema_data(
                connection_hash, 
                schema_data, 
                ttl_hours * 3600
            )
            
            return str(schema_cache.id)
            
        except Exception as e:
            self.logger.error(f"Failed to cache schema data: {str(e)}")
            session.rollback()
            raise
    
    def get_cached_schema_data(self, connection_string: str) -> Optional[Dict[str, Any]]:
        """
        Get cached schema data
        
        Args:
            connection_string: Connection string
            
        Returns:
            Cached schema data or None
        """
        try:
            connection_hash = self.generate_connection_hash(connection_string)
            
            # Check Redis cache first
            schema_data = self.redis_service.get_cached_schema_data(connection_hash)
            if schema_data:
                return schema_data
            
            # Fallback to database
            db_manager = get_database_manager()
            with db_manager.get_session() as session:
                schema_cache = session.query(SchemaCache).filter(
                    SchemaCache.connection_string_hash == connection_hash,
                    SchemaCache.expires_at > datetime.utcnow()
                ).first()
                
                if schema_cache:
                    return schema_cache.schema_data
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get cached schema data: {str(e)}")
            return None
    
    def cleanup_expired_data(self, session: Session) -> Dict[str, int]:
        """
        Clean up expired data from the database
        
        Args:
            session: Database session
            
        Returns:
            Dictionary with cleanup results
        """
        try:
            now = datetime.utcnow()
            cleanup_results = {}
            
            # Clean up expired schema cache
            expired_schemas = session.query(SchemaCache).filter(
                SchemaCache.expires_at < now
            ).delete()
            cleanup_results["expired_schemas"] = expired_schemas
            
            # Clean up expired user sessions
            expired_sessions = session.query(UserSession).filter(
                UserSession.expires_at < now
            ).delete()
            cleanup_results["expired_sessions"] = expired_sessions
            
            # Clean up old system logs (older than 30 days)
            old_logs = session.query(SystemLog).filter(
                SystemLog.created_at < now - timedelta(days=30)
            ).delete()
            cleanup_results["old_logs"] = old_logs
            
            session.commit()
            
            self.logger.info(f"Cleanup completed: {cleanup_results}")
            return cleanup_results
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup expired data: {str(e)}")
            session.rollback()
            raise
    
    def get_database_stats(self, session: Session) -> Dict[str, Any]:
        """
        Get database statistics
        
        Args:
            session: Database session
            
        Returns:
            Database statistics
        """
        try:
            stats = {}
            
            # Count records in each table
            stats["query_history_count"] = session.query(QueryHistory).count()
            stats["document_metadata_count"] = session.query(DocumentMetadata).count()
            stats["schema_cache_count"] = session.query(SchemaCache).count()
            stats["performance_metrics_count"] = session.query(PerformanceMetrics).count()
            stats["user_sessions_count"] = session.query(UserSession).count()
            stats["system_logs_count"] = session.query(SystemLog).count()
            
            # Get recent activity
            recent_queries = session.query(QueryHistory).filter(
                QueryHistory.created_at > datetime.utcnow() - timedelta(hours=24)
            ).count()
            stats["recent_queries_24h"] = recent_queries
            
            # Get cache hit rate
            total_queries = session.query(QueryHistory).count()
            cached_queries = session.query(QueryHistory).filter(
                QueryHistory.cache_hit == True
            ).count()
            
            if total_queries > 0:
                stats["cache_hit_rate"] = cached_queries / total_queries
            else:
                stats["cache_hit_rate"] = 0
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get database stats: {str(e)}")
            raise
    
    def backup_database_data(self, session: Session) -> Dict[str, Any]:
        """
        Create a backup of important database data
        
        Args:
            session: Database session
            
        Returns:
            Backup data
        """
        try:
            backup_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "query_history": [],
                "document_metadata": [],
                "performance_metrics": []
            }
            
            # Backup recent queries (last 7 days)
            recent_queries = session.query(QueryHistory).filter(
                QueryHistory.created_at > datetime.utcnow() - timedelta(days=7)
            ).all()
            
            for query in recent_queries:
                backup_data["query_history"].append(query.to_dict())
            
            # Backup document metadata
            documents = session.query(DocumentMetadata).all()
            for doc in documents:
                backup_data["document_metadata"].append(doc.to_dict())
            
            # Backup performance metrics (last 7 days)
            recent_metrics = session.query(PerformanceMetrics).filter(
                PerformanceMetrics.recorded_at > datetime.utcnow() - timedelta(days=7)
            ).all()
            
            for metric in recent_metrics:
                backup_data["performance_metrics"].append(metric.to_dict())
            
            return backup_data
            
        except Exception as e:
            self.logger.error(f"Failed to backup database data: {str(e)}")
            raise

# Global database utils instance
db_utils: Optional[DatabaseUtils] = None

def get_database_utils() -> DatabaseUtils:
    """Get the global database utils instance"""
    if db_utils is None:
        raise RuntimeError("Database utils not initialized")
    return db_utils

def initialize_database_utils() -> DatabaseUtils:
    """Initialize the global database utils"""
    global db_utils
    db_utils = DatabaseUtils()
    return db_utils
