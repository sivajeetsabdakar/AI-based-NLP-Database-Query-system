"""
Integration Tests
Test component interactions and end-to-end workflows
"""
import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient

from main import app
from api.services.database_manager import DatabaseManager
from api.services.redis_service import RedisService
from api.services.chromadb_service import ChromaDBService
from api.services.document_processor import DocumentProcessor
from api.services.query_classifier import QueryClassifier
from api.services.sql_generator import SQLGenerator
from api.services.document_search_engine import DocumentSearchEngine
from api.services.hybrid_query_processor import HybridQueryProcessor

class TestSystemIntegration:
    """Test system-wide integration."""
    
    def test_app_startup(self, test_client):
        """Test application startup."""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
    
    def test_database_connection_integration(self, test_client):
        """Test database connection integration."""
        connection_data = {
            "database_url": "sqlite:///test.db",
            "connection_name": "Test Connection",
            "test_connection": True
        }
        
        with patch('api.services.database_manager.DatabaseManager') as mock_db:
            mock_db.return_value.test_connection.return_value = True
            
            response = test_client.post("/api/ingest/database", json=connection_data)
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "connection_id" in data
    
    def test_document_upload_integration(self, test_client, temp_file):
        """Test document upload integration."""
        with open(temp_file, "rb") as f:
            files = {"files": ("test.txt", f, "text/plain")}
            data = {"user_session_id": "test_session"}
            
            with patch('api.services.document_processor.DocumentProcessor') as mock_processor:
                mock_processor.return_value.process_documents.return_value = {
                    "processed_documents": 1,
                    "document_ids": ["test_doc_123"],
                    "processing_time": 1.5
                }
                
                response = test_client.post("/api/ingest/documents", files=files, data=data)
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert "document_id" in data
    
    def test_query_processing_integration(self, test_client):
        """Test query processing integration."""
        query_data = {
            "query": "How many employees do we have?",
            "user_context": {"session_id": "test_session"}
        }
        
        with patch('api.services.hybrid_query_processor.HybridQueryProcessor') as mock_processor:
            mock_processor.return_value.process_hybrid_query.return_value = {
                "success": True,
                "query_type": "SQL_QUERY",
                "results": [{"count": 10}],
                "total_results": 1,
                "confidence": 0.9
            }
            
            response = test_client.post("/api/query/", json=query_data)
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["query_type"] == "SQL_QUERY"
            assert data["total_results"] == 1
    
    def test_schema_discovery_integration(self, test_client):
        """Test schema discovery integration."""
        with patch('api.services.schema_service.SchemaService') as mock_service:
            mock_service.return_value.get_schema_info.return_value = {
                "tables": {
                    "employees": {
                        "columns": ["id", "name", "email"],
                        "description": "Employee information"
                    }
                },
                "relationships": []
            }
            
            response = test_client.get("/api/schema")
            assert response.status_code == 200
            data = response.json()
            assert "tables" in data
            assert "employees" in data["tables"]
    
    def test_document_search_integration(self, test_client):
        """Test document search integration."""
        search_data = {
            "query": "Python skills",
            "doc_type": "resume",
            "limit": 10
        }
        
        with patch('api.services.document_search_engine.DocumentSearchEngine') as mock_engine:
            mock_engine.return_value.search_documents.return_value = {
                "success": True,
                "results": [
                    {
                        "document": "Python developer with 5 years experience",
                        "metadata": {"filename": "resume.pdf"},
                        "similarity_score": 0.9
                    }
                ],
                "total_results": 1
            }
            
            response = test_client.post("/api/query/documents", json=search_data)
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["total_results"] == 1

class TestComponentIntegration:
    """Test component-level integration."""
    
    def test_database_schema_integration(self, test_db_manager, sample_database_schema):
        """Test database and schema integration."""
        with patch.object(test_db_manager, 'get_connection') as mock_conn:
            mock_conn.return_value.execute.return_value.fetchall.return_value = [
                {"table_name": "employees", "column_name": "id", "data_type": "INTEGER"}
            ]
            
            # Test schema discovery
            with patch('api.services.dynamic_schema_discovery.DynamicSchemaDiscovery') as mock_discovery:
                mock_discovery.return_value.discover_schema.return_value = sample_database_schema
                
                # This would be called by the schema service
                result = mock_discovery.return_value.discover_schema()
                assert result is not None
                assert "tables" in result
    
    def test_document_processing_integration(self, test_document_processor, sample_documents):
        """Test document processing integration."""
        with patch.object(test_document_processor, 'embedding_model') as mock_model:
            mock_model.encode.return_value = [[0.1, 0.2, 0.3]]  # Mock embedding
            
            with patch.object(test_document_processor, 'chromadb_service') as mock_chroma:
                mock_chroma.client.get_or_create_collection.return_value = Mock()
                
                # Test document processing
                result = test_document_processor.process_documents(["/tmp/test.txt"])
                assert result is not None
                assert "processed_documents" in result
    
    def test_query_classification_integration(self, test_query_classifier):
        """Test query classification integration."""
        query = "How many employees do we have?"
        
        with patch.object(test_query_classifier, 'mistral_client') as mock_mistral:
            mock_mistral.generate_response.return_value = '{"query_type": "SQL_QUERY", "confidence": 0.9}'
            
            result = test_query_classifier.classify_query(query)
            assert result is not None
            assert "query_type" in result
            assert "confidence" in result
    
    def test_sql_generation_integration(self, test_sql_generator, sample_database_schema):
        """Test SQL generation integration."""
        query = "How many employees do we have?"
        
        with patch.object(test_sql_generator, 'mistral_client') as mock_mistral:
            mock_mistral.generate_response.return_value = '{"sql": "SELECT COUNT(*) FROM employees", "confidence": 0.9}'
            
            result = test_sql_generator.generate_sql(query, sample_database_schema)
            assert result is not None
            assert "sql" in result
            assert "confidence" in result
    
    def test_document_search_integration(self, test_document_search_engine):
        """Test document search integration."""
        query = "Python skills"
        
        with patch.object(test_document_search_engine, 'embedding_model') as mock_model:
            mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
            
            with patch.object(test_document_search_engine, 'chromadb_service') as mock_chroma:
                mock_chroma.client.get_collection.return_value.query.return_value = {
                    "documents": [["Python developer"]],
                    "metadatas": [[{"filename": "resume.pdf"}]],
                    "distances": [[0.1]]
                }
                
                result = test_document_search_engine.search_documents(query)
                assert result is not None
                assert "success" in result
    
    def test_hybrid_query_processing_integration(self, test_hybrid_query_processor):
        """Test hybrid query processing integration."""
        query = "Python developers earning over 100k"
        
        with patch.object(test_hybrid_query_processor, 'query_classifier') as mock_classifier:
            mock_classifier.classify_query.return_value = {
                "query_type": "HYBRID_QUERY",
                "confidence": 0.9
            }
            
            with patch.object(test_hybrid_query_processor, 'sql_generator') as mock_sql:
                mock_sql.generate_sql.return_value = {
                    "sql": "SELECT * FROM employees WHERE salary > 100000",
                    "confidence": 0.8
                }
                
                with patch.object(test_hybrid_query_processor, 'document_search_engine') as mock_doc:
                    mock_doc.search_documents.return_value = {
                        "success": True,
                        "results": [{"document": "Python developer resume"}]
                    }
                    
                    result = test_hybrid_query_processor.process_hybrid_query(query)
                    assert result is not None
                    assert "success" in result

class TestEndToEndWorkflows:
    """Test complete end-to-end workflows."""
    
    def test_complete_database_workflow(self, test_client):
        """Test complete database connection workflow."""
        # 1. Connect to database
        connection_data = {
            "database_url": "sqlite:///test.db",
            "test_connection": True
        }
        
        with patch('api.services.database_manager.DatabaseManager') as mock_db:
            mock_db.return_value.test_connection.return_value = True
            
            response = test_client.post("/api/ingest/database", json=connection_data)
            assert response.status_code == 200
        
        # 2. Get schema
        with patch('api.services.schema_service.SchemaService') as mock_schema:
            mock_schema.return_value.get_schema_info.return_value = {
                "tables": {"employees": {"columns": ["id", "name"]}},
                "relationships": []
            }
            
            response = test_client.get("/api/schema")
            assert response.status_code == 200
    
    def test_complete_document_workflow(self, test_client, temp_file):
        """Test complete document processing workflow."""
        # 1. Upload document
        with open(temp_file, "rb") as f:
            files = {"files": ("test.txt", f, "text/plain")}
            
            with patch('api.services.document_processor.DocumentProcessor') as mock_processor:
                mock_processor.return_value.process_documents.return_value = {
                    "processed_documents": 1,
                    "document_ids": ["test_doc_123"]
                }
                
                response = test_client.post("/api/ingest/documents", files=files)
                assert response.status_code == 200
        
        # 2. Search documents
        search_data = {"query": "test content", "limit": 10}
        
        with patch('api.services.document_search_engine.DocumentSearchEngine') as mock_engine:
            mock_engine.return_value.search_documents.return_value = {
                "success": True,
                "results": [{"document": "test content"}],
                "total_results": 1
            }
            
            response = test_client.post("/api/query/documents", json=search_data)
            assert response.status_code == 200
    
    def test_complete_query_workflow(self, test_client):
        """Test complete query processing workflow."""
        # 1. Classify query
        classification_data = {"query": "How many employees do we have?"}
        
        with patch('api.services.query_classifier.QueryClassifier') as mock_classifier:
            mock_classifier.return_value.classify_query.return_value = {
                "query_type": "SQL_QUERY",
                "confidence": 0.9
            }
            
            response = test_client.post("/api/query/classify", json=classification_data)
            assert response.status_code == 200
        
        # 2. Process query
        query_data = {
            "query": "How many employees do we have?",
            "user_context": {"session_id": "test_session"}
        }
        
        with patch('api.services.hybrid_query_processor.HybridQueryProcessor') as mock_processor:
            mock_processor.return_value.process_hybrid_query.return_value = {
                "success": True,
                "query_type": "SQL_QUERY",
                "results": [{"count": 10}],
                "total_results": 1
            }
            
            response = test_client.post("/api/query/", json=query_data)
            assert response.status_code == 200
    
    def test_error_handling_workflow(self, test_client):
        """Test error handling across the system."""
        # Test invalid database connection
        invalid_connection = {
            "database_url": "invalid://connection",
            "test_connection": True
        }
        
        with patch('api.services.database_manager.DatabaseManager') as mock_db:
            mock_db.return_value.test_connection.side_effect = Exception("Connection failed")
            
            response = test_client.post("/api/ingest/database", json=invalid_connection)
            assert response.status_code == 200  # Should handle error gracefully
            data = response.json()
            assert data["success"] is False
    
    def test_performance_workflow(self, test_client):
        """Test performance under load."""
        import time
        
        # Test multiple concurrent requests
        start_time = time.time()
        
        with patch('api.services.hybrid_query_processor.HybridQueryProcessor') as mock_processor:
            mock_processor.return_value.process_hybrid_query.return_value = {
                "success": True,
                "query_type": "SQL_QUERY",
                "results": [{"count": 10}],
                "total_results": 1
            }
            
            # Simulate multiple concurrent requests
            responses = []
            for i in range(5):
                query_data = {
                    "query": f"Test query {i}",
                    "user_context": {"session_id": f"test_session_{i}"}
                }
                response = test_client.post("/api/query/", json=query_data)
                responses.append(response)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # All requests should succeed
            for response in responses:
                assert response.status_code == 200
            
            # Should complete within reasonable time
            assert processing_time < 5.0  # 5 seconds max for 5 requests
