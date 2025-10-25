#!/usr/bin/env python3
"""
Test script for database utils initialization
"""
import sys
import os
import logging
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.services.database_initializer import initialize_database_services
from api.services.database_utils import get_database_utils

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_utils_initialization():
    """Test database utils initialization"""
    try:
        logger.info("Testing database utils initialization...")
        
        # Initialize database services
        logger.info("Initializing database services...")
        db_initializer = initialize_database_services()
        result = db_initializer.initialize_all_services()
        
        if result["status"] != "success":
            logger.error(f"Database initialization failed: {result.get('error')}")
            return False
        
        logger.info("Database services initialized successfully")
        
        # Test database utils access
        logger.info("Testing database utils access...")
        try:
            db_utils = get_database_utils()
            logger.info("Database utils accessed successfully!")
            
            # Test some basic functionality
            test_query = "SELECT 1 as test"
            query_hash = db_utils.generate_query_hash(test_query, "sql")
            logger.info(f"Query hash generated: {query_hash}")
            
            # Test connection hash
            test_connection = "postgresql://admin:password@localhost:5432/employee_nlp_db"
            connection_hash = db_utils.generate_connection_hash(test_connection)
            logger.info(f"Connection hash generated: {connection_hash}")
            
        except Exception as e:
            logger.error(f"Failed to access database utils: {str(e)}")
            return False
        
        logger.info("Database utils initialization test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        return False

def test_database_utils_functionality():
    """Test database utils functionality"""
    try:
        logger.info("Testing database utils functionality...")
        
        db_utils = get_database_utils()
        
        # Test query hash generation
        test_queries = [
            ("SELECT * FROM employees", "sql"),
            ("Find Python developers", "document"),
            ("Python developers with salary > 100k", "hybrid")
        ]
        
        for query, query_type in test_queries:
            hash_result = db_utils.generate_query_hash(query, query_type)
            logger.info(f"Query: '{query}' -> Hash: {hash_result}")
        
        # Test connection hash generation
        test_connections = [
            "postgresql://admin:password@localhost:5432/employee_nlp_db",
            "postgresql://user:pass@remote:5432/test_db",
            "sqlite:///test.db"
        ]
        
        for connection in test_connections:
            hash_result = db_utils.generate_connection_hash(connection)
            logger.info(f"Connection: '{connection}' -> Hash: {hash_result}")
        
        logger.info("Database utils functionality test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Functionality test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Database Utils Initialization Test")
    print("=" * 60)
    
    # Test initialization
    success1 = test_database_utils_initialization()
    
    print("\n" + "=" * 60)
    print("Database Utils Functionality Test")
    print("=" * 60)
    
    # Test functionality
    success2 = test_database_utils_functionality()
    
    overall_success = success1 and success2
    print(f"\nOverall test result: {'PASSED' if overall_success else 'FAILED'}")
    sys.exit(0 if overall_success else 1)
