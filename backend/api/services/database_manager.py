"""
Database Connection Manager
Handles PostgreSQL database connections with pooling and health checks
"""
import asyncio
import logging
from typing import Optional, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import asynccontextmanager
import time

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, database_url: str):
        """
        Initialize database manager with connection pooling
        
        Args:
            database_url: PostgreSQL connection string
        """
        self.database_url = database_url
        self.engine = None
        self.async_engine = None
        self.session_factory = None
        self.async_session_factory = None
        self.logger = logger
        
    def initialize(self):
        """Initialize database connections and session factories"""
        try:
            # Create synchronous engine with connection pooling
            self.engine = create_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False
            )
            
            # Create async engine for async operations
            async_url = self.database_url.replace("postgresql://", "postgresql+asyncpg://")
            self.async_engine = create_async_engine(
                async_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False
            )
            
            # Create session factories
            self.session_factory = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False
            )
            
            self.async_session_factory = sessionmaker(
                bind=self.async_engine,
                class_=AsyncSession,
                autocommit=False,
                autoflush=False
            )
            
            self.logger.info("Database manager initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database manager: {str(e)}")
            raise
    
    def get_session(self) -> Session:
        """Get a database session"""
        if not self.session_factory:
            raise RuntimeError("Database manager not initialized")
        return self.session_factory()
    
    def get_connection(self):
        """
        Get a database connection (wrapper for backward compatibility with tests)
        Returns the engine's connection
        """
        if not self.engine:
            raise RuntimeError("Database manager not initialized")
        return self.engine.connect()
    
    @asynccontextmanager
    async def get_async_session(self):
        """Get an async database session with context manager"""
        if not self.async_session_factory:
            raise RuntimeError("Database manager not initialized")
        
        async with self.async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform database health check
        
        Returns:
            Health check results
        """
        try:
            start_time = time.time()
            
            with self.get_session() as session:
                # Test basic connectivity
                result = session.execute(text("SELECT 1")).scalar()
                
                # Test connection pool status
                pool_status = {
                    "pool_size": self.engine.pool.size(),
                    "checked_in": self.engine.pool.checkedin(),
                    "checked_out": self.engine.pool.checkedout(),
                    "overflow": self.engine.pool.overflow()
                }
                
                response_time = time.time() - start_time
                
                return {
                    "status": "healthy",
                    "response_time": response_time,
                    "pool_status": pool_status,
                    "timestamp": time.time()
                }
                
        except Exception as e:
            self.logger.error(f"Database health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
    
    async def async_health_check(self) -> Dict[str, Any]:
        """
        Perform async database health check
        
        Returns:
            Health check results
        """
        try:
            start_time = time.time()
            
            async with self.get_async_session() as session:
                # Test basic connectivity
                result = await session.execute(text("SELECT 1"))
                await result.scalar()
                
                response_time = time.time() - start_time
                
                return {
                    "status": "healthy",
                    "response_time": response_time,
                    "timestamp": time.time()
                }
                
        except Exception as e:
            self.logger.error(f"Async database health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
    
    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get database connection information
        
        Returns:
            Connection information
        """
        return {
            "database_url": self.database_url.split("@")[-1] if "@" in self.database_url else "hidden",
            "pool_size": self.engine.pool.size() if self.engine else 0,
            "max_overflow": self.engine.pool._max_overflow if self.engine else 0,
            "pool_recycle": self.engine.pool._recycle if self.engine else 0,
            "pool_pre_ping": self.engine.pool._pre_ping if self.engine else False
        }
    
    def close(self):
        """Close all database connections"""
        try:
            if self.engine:
                self.engine.dispose()
            if self.async_engine:
                asyncio.create_task(self.async_engine.dispose())
            self.logger.info("Database connections closed")
        except Exception as e:
            self.logger.error(f"Error closing database connections: {str(e)}")

# Global database manager instance
db_manager: Optional[DatabaseManager] = None

def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance"""
    if db_manager is None:
        raise RuntimeError("Database manager not initialized")
    return db_manager

def initialize_database_manager(database_url: str) -> DatabaseManager:
    """Initialize the global database manager"""
    global db_manager
    db_manager = DatabaseManager(database_url)
    db_manager.initialize()
    return db_manager
