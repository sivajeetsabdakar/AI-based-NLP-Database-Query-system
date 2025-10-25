"""
Database Initialization Service
Handles initialization of all database services and connections
"""
import logging
from typing import Dict, Any, Optional
from .database_manager import initialize_database_manager, get_database_manager
from .chromadb_service import initialize_chromadb_service, get_chromadb_service
from .redis_service import initialize_redis_service, get_redis_service
from .database_utils import initialize_database_utils
from config import settings

logger = logging.getLogger(__name__)

class DatabaseInitializer:
    """Handles initialization of all database services"""
    
    def __init__(self):
        self.logger = logger
        self.initialized = False
        self.services = {}
    
    def initialize_all_services(self) -> Dict[str, Any]:
        """
        Initialize all database services
        
        Returns:
            Dictionary with initialization results
        """
        try:
            self.logger.info("Starting database services initialization...")
            
            # Initialize PostgreSQL database manager
            self.logger.info("Initializing PostgreSQL database manager...")
            db_manager = initialize_database_manager(settings.DATABASE_URL)
            self.services["postgresql"] = db_manager
            
            # Initialize ChromaDB service
            self.logger.info("Initializing ChromaDB service...")
            chromadb_service = initialize_chromadb_service(settings.CHROMA_URL)
            self.services["chromadb"] = chromadb_service
            
            # Initialize Redis service
            self.logger.info("Initializing Redis service...")
            redis_service = initialize_redis_service(settings.REDIS_URL)
            self.services["redis"] = redis_service
            
            # Initialize Database Utils service
            self.logger.info("Initializing Database Utils service...")
            db_utils = initialize_database_utils()
            self.services["database_utils"] = db_utils
            
            # Perform health checks
            self.logger.info("Performing health checks...")
            health_results = self._perform_health_checks()
            
            self.initialized = True
            self.logger.info("All database services initialized successfully")
            
            return {
                "status": "success",
                "services": list(self.services.keys()),
                "health_checks": health_results,
                "initialized": True
            }
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database services: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "initialized": False
            }
    
    def _perform_health_checks(self) -> Dict[str, Any]:
        """Perform health checks on all services"""
        health_results = {}
        
        try:
            # PostgreSQL health check
            db_manager = get_database_manager()
            health_results["postgresql"] = db_manager.health_check()
            
        except Exception as e:
            self.logger.error(f"PostgreSQL health check failed: {str(e)}")
            health_results["postgresql"] = {"status": "error", "error": str(e)}
        
        try:
            # ChromaDB health check
            chromadb_service = get_chromadb_service()
            health_results["chromadb"] = chromadb_service.health_check()
            
        except Exception as e:
            self.logger.error(f"ChromaDB health check failed: {str(e)}")
            health_results["chromadb"] = {"status": "error", "error": str(e)}
        
        try:
            # Redis health check
            redis_service = get_redis_service()
            health_results["redis"] = redis_service.health_check()
            
        except Exception as e:
            self.logger.error(f"Redis health check failed: {str(e)}")
            health_results["redis"] = {"status": "error", "error": str(e)}
        
        return health_results
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all database services"""
        if not self.initialized:
            return {"status": "not_initialized"}
        
        try:
            status = {
                "initialized": self.initialized,
                "services": {},
                "health_checks": self._perform_health_checks()
            }
            
            # Get service-specific information
            try:
                db_manager = get_database_manager()
                status["services"]["postgresql"] = db_manager.get_connection_info()
            except Exception as e:
                status["services"]["postgresql"] = {"error": str(e)}
            
            try:
                redis_service = get_redis_service()
                status["services"]["redis"] = redis_service.get_cache_stats()
            except Exception as e:
                status["services"]["redis"] = {"error": str(e)}
            
            try:
                chromadb_service = get_chromadb_service()
                status["services"]["chromadb"] = chromadb_service.get_all_collections()
            except Exception as e:
                status["services"]["chromadb"] = {"error": str(e)}
            
            return status
            
        except Exception as e:
            self.logger.error(f"Failed to get service status: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def close_all_services(self):
        """Close all database services"""
        try:
            self.logger.info("Closing all database services...")
            
            # Close PostgreSQL connections
            if "postgresql" in self.services:
                self.services["postgresql"].close()
            
            # Redis and ChromaDB connections are managed by their clients
            # No explicit close needed
            
            self.initialized = False
            self.logger.info("All database services closed")
            
        except Exception as e:
            self.logger.error(f"Error closing database services: {str(e)}")

# Global database initializer instance
db_initializer: Optional[DatabaseInitializer] = None

def get_database_initializer() -> DatabaseInitializer:
    """Get the global database initializer instance"""
    if db_initializer is None:
        raise RuntimeError("Database initializer not initialized")
    return db_initializer

def initialize_database_services() -> DatabaseInitializer:
    """Initialize all database services"""
    global db_initializer
    db_initializer = DatabaseInitializer()
    return db_initializer
