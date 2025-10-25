"""
Pytest Configuration
Test fixtures and configuration for the NLP Query Engine
"""
import pytest
import asyncio
import os
import tempfile
from typing import Dict, Any, Optional
from unittest.mock import Mock, patch, MagicMock
import json

# Set test environment
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///test.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"
os.environ["CHROMA_URL"] = "http://localhost:8001"
os.environ["MISTRAL_API_KEY"] = "test_key"

from api.services.database_manager import DatabaseManager
from api.services.redis_service import RedisService
from api.services.chromadb_service import ChromaDBService
from api.services.mistral_client import MistralClient
from api.services.schema_service import SchemaService
from api.services.document_processor import DocumentProcessor
from api.services.query_classifier import QueryClassifier
from api.services.sql_generator import SQLGenerator
from api.services.document_search_engine import DocumentSearchEngine
from api.services.hybrid_query_processor import HybridQueryProcessor

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_db_manager():
    """Create a test database manager."""
    # DatabaseManager requires database_url argument
    return DatabaseManager(database_url=os.environ.get("DATABASE_URL", "sqlite:///test.db"))

@pytest.fixture
def test_redis_service():
    """Create a test Redis service."""
    service = RedisService(redis_url=os.environ.get("REDIS_URL", "redis://localhost:6379/1"))
    # Mock the client attribute for tests
    if not hasattr(service, 'client'):
        service.client = Mock()
        service.client.get.return_value = None
        service.client.set.return_value = True
        service.client.ping.return_value = True
    return service

@pytest.fixture
def test_chromadb_service():
    """Create a test ChromaDB service."""
    service = ChromaDBService(chroma_url=os.environ.get("CHROMA_URL", "http://localhost:8001"))
    # Mock the client attribute for tests
    if not hasattr(service, 'client'):
        service.client = Mock()
    return service

@pytest.fixture
def test_mistral_client():
    """Create a test Mistral client."""
    return MistralClient()

@pytest.fixture
def test_schema_service():
    """Create a test schema service."""
    return SchemaService()

@pytest.fixture
def test_document_processor():
    """Create a test document processor."""
    return DocumentProcessor()

@pytest.fixture
def test_query_classifier():
    """Create a test query classifier."""
    return QueryClassifier()

@pytest.fixture
def test_sql_generator():
    """Create a test SQL generator."""
    return SQLGenerator()

@pytest.fixture
def test_document_search_engine():
    """Create a test document search engine."""
    engine = DocumentSearchEngine()
    # Mock the embedding_model attribute for tests
    if not hasattr(engine, 'embedding_model'):
        engine.embedding_model = Mock()
        engine.embedding_model.encode.return_value = [[0.1] * 384]  # Mock 384-dim embeddings
    return engine

@pytest.fixture
def test_hybrid_query_processor():
    """Create a test hybrid query processor."""
    return HybridQueryProcessor()

@pytest.fixture
def sample_database_schema():
    """Sample database schema for testing."""
    return {
        "tables": {
            "employees": {
                "columns": [
                    {"name": "id", "type": "INTEGER", "primary_key": True},
                    {"name": "name", "type": "VARCHAR(100)", "nullable": False},
                    {"name": "email", "type": "VARCHAR(255)", "unique": True},
                    {"name": "department", "type": "VARCHAR(50)"},
                    {"name": "position", "type": "VARCHAR(100)"},
                    {"name": "salary", "type": "DECIMAL(10,2)"},
                    {"name": "hire_date", "type": "DATE"}
                ],
                "description": "Employee information table"
            },
            "departments": {
                "columns": [
                    {"name": "id", "type": "INTEGER", "primary_key": True},
                    {"name": "name", "type": "VARCHAR(100)", "nullable": False},
                    {"name": "description", "type": "TEXT"},
                    {"name": "manager_id", "type": "INTEGER"}
                ],
                "description": "Department information table"
            }
        },
        "relationships": [
            {
                "from_table": "employees",
                "from_column": "department",
                "to_table": "departments",
                "to_column": "id",
                "type": "foreign_key"
            }
        ]
    }

@pytest.fixture
def sample_documents():
    """Sample documents for testing."""
    return [
        {
            "filename": "resume_john_doe.pdf",
            "content": "John Doe\nSoftware Engineer\nPython, JavaScript, React\n5 years experience",
            "type": "resume",
            "metadata": {
                "author": "John Doe",
                "created_at": "2024-01-15",
                "skills": ["Python", "JavaScript", "React"]
            }
        },
        {
            "filename": "contract_employment.docx",
            "content": "Employment Contract\nEmployee: Jane Smith\nPosition: Data Scientist\nSalary: $120,000",
            "type": "contract",
            "metadata": {
                "employee": "Jane Smith",
                "position": "Data Scientist",
                "salary": 120000
            }
        }
    ]

@pytest.fixture
def sample_queries():
    """Sample queries for testing."""
    return [
        {
            "query": "How many employees do we have?",
            "type": "SQL_QUERY",
            "expected_sql": "SELECT COUNT(*) FROM employees",
            "expected_results": [{"count": 10}]
        },
        {
            "query": "Show me resumes with Python skills",
            "type": "DOCUMENT_QUERY",
            "expected_results": ["resume_john_doe.pdf"]
        },
        {
            "query": "Python developers earning over 100k",
            "type": "HYBRID_QUERY",
            "expected_sql": "SELECT * FROM employees WHERE salary > 100000",
            "expected_documents": ["resume_john_doe.pdf"]
        }
    ]

@pytest.fixture
def mock_mistral_response():
    """Mock Mistral API response."""
    return {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "query_type": "SQL_QUERY",
                        "confidence": 0.9,
                        "reasoning": "Query asks for count of employees",
                        "entities": ["employees"],
                        "intent": "count",
                        "complexity": "simple"
                    })
                }
            }
        ]
    }

@pytest.fixture
def test_app():
    """Create a test FastAPI application."""
    from main import app
    return app

@pytest.fixture
def test_client(test_app):
    """Create a test client."""
    from fastapi.testclient import TestClient
    return TestClient(test_app)

@pytest.fixture
def temp_file():
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as f:
        f.write(b"Test document content")
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def temp_pdf_file():
    """Create a temporary PDF file for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as f:
        # Write minimal PDF content
        f.write(b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n")
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def mock_database_connection():
    """Mock database connection."""
    mock_conn = Mock()
    mock_conn.execute.return_value.fetchall.return_value = [
        {"id": 1, "name": "John Doe", "email": "john@example.com"},
        {"id": 2, "name": "Jane Smith", "email": "jane@example.com"}
    ]
    return mock_conn

@pytest.fixture
def mock_chromadb_collection():
    """Mock ChromaDB collection."""
    mock_collection = Mock()
    mock_collection.add.return_value = None
    mock_collection.query.return_value = {
        "documents": [["Test document content"]],
        "metadatas": [[{"filename": "test.txt"}]],
        "distances": [[0.1]]
    }
    mock_collection.count.return_value = 10
    return mock_collection

@pytest.fixture
def mock_redis_client():
    """Mock Redis client."""
    mock_redis = Mock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    mock_redis.scan_iter.return_value = []
    return mock_redis

@pytest.fixture
def integration_test_data():
    """Integration test data."""
    return {
        "database_url": "sqlite:///test_integration.db",
        "documents": [
            {
                "filename": "test_resume.pdf",
                "content": "Software Engineer with Python experience",
                "type": "resume"
            }
        ],
        "queries": [
            "How many employees do we have?",
            "Find resumes with Python skills",
            "Python developers earning over 100k"
        ],
        "expected_results": {
            "sql_queries": 1,
            "document_queries": 1,
            "hybrid_queries": 1
        }
    }

# Test utilities
class TestUtils:
    """Test utility functions."""
    
    @staticmethod
    def create_test_document(filename: str, content: str, doc_type: str = "general") -> Dict[str, Any]:
        """Create a test document."""
        return {
            "filename": filename,
            "content": content,
            "type": doc_type,
            "metadata": {
                "created_at": "2024-01-01",
                "size": len(content)
            }
        }
    
    @staticmethod
    def create_test_query(query: str, query_type: str = "SQL_QUERY") -> Dict[str, Any]:
        """Create a test query."""
        return {
            "query": query,
            "query_type": query_type,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    
    @staticmethod
    def assert_response_structure(response: Dict[str, Any], required_fields: list):
        """Assert response has required structure."""
        for field in required_fields:
            assert field in response, f"Missing required field: {field}"
    
    @staticmethod
    def assert_success_response(response: Dict[str, Any]):
        """Assert response indicates success."""
        assert response.get("success", False), f"Expected success=True, got: {response}"
    
    @staticmethod
    def assert_error_response(response: Dict[str, Any]):
        """Assert response indicates error."""
        assert not response.get("success", True), f"Expected success=False, got: {response}"
        assert "error" in response, f"Expected error field, got: {response}"

@pytest.fixture
def test_utils():
    """Test utilities fixture."""
    return TestUtils()
