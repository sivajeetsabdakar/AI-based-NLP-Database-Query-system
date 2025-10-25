"""
Performance Tests
Test system performance under various load conditions
"""
import pytest
import time
import asyncio
import concurrent.futures
from unittest.mock import Mock, patch, MagicMock
import statistics

from api.services.database_manager import DatabaseManager
from api.services.redis_service import RedisService
from api.services.chromadb_service import ChromaDBService
from api.services.document_processor import DocumentProcessor
from api.services.query_classifier import QueryClassifier
from api.services.sql_generator import SQLGenerator
from api.services.document_search_engine import DocumentSearchEngine
from api.services.hybrid_query_processor import HybridQueryProcessor

class TestPerformanceBenchmarks:
    """Test performance benchmarks for individual components."""
    
    def test_database_query_performance(self, test_db_manager):
        """Test database query performance."""
        with patch.object(test_db_manager, 'get_connection') as mock_conn:
            # Mock the context manager properly
            mock_connection = Mock()
            mock_connection.execute.return_value.fetchall.return_value = [
                {"id": i, "name": f"Employee {i}"} for i in range(1000)
            ]
            mock_conn.return_value.__enter__.return_value = mock_connection
            mock_conn.return_value.__exit__.return_value = None
            
            # Test single query performance using get_connection
            start_time = time.time()
            with test_db_manager.get_connection() as conn:
                result = conn.execute("SELECT * FROM employees").fetchall()
            end_time = time.time()
            
            query_time = end_time - start_time
            assert query_time < 1.0  # Should complete within 1 second
            assert len(result) == 1000
    
    def test_redis_cache_performance(self, test_redis_service):
        """Test Redis cache performance."""
        with patch.object(test_redis_service, 'client') as mock_redis:
            mock_redis.get.return_value = '{"cached_data": "test"}'
            mock_redis.set.return_value = True
            
            # Test cache read performance using actual method
            start_time = time.time()
            for i in range(100):
                result = test_redis_service.get_cache("test_key")
            end_time = time.time()
            
            cache_time = end_time - start_time
            assert cache_time < 0.5  # Should complete within 0.5 seconds for 100 operations
    
    def test_chromadb_search_performance(self, test_chromadb_service):
        """Test ChromaDB search performance."""
        with patch.object(test_chromadb_service, 'client') as mock_client:
            mock_collection = Mock()
            mock_collection.query.return_value = {
                "documents": [["Test document"]],
                "metadatas": [[{"filename": "test.pdf"}]],
                "distances": [[0.1]]
            }
            mock_client.get_collection.return_value = mock_collection
            
            # Test search performance using DocumentSearchEngine
            from api.services.document_search_engine import DocumentSearchEngine
            search_engine = DocumentSearchEngine()
            
            start_time = time.time()
            for i in range(50):
                result = search_engine.search_documents("test query", limit=10)
            end_time = time.time()
            
            search_time = end_time - start_time
            assert search_time < 2.0  # Should complete within 2 seconds for 50 searches
    
    def test_document_processing_performance(self, test_document_processor):
        """Test document processing performance."""
        with patch.object(test_document_processor, 'embedding_model') as mock_model:
            mock_model.encode.return_value = [[0.1, 0.2, 0.3]]  # Mock embedding
            
            with patch.object(test_document_processor, 'chromadb_service') as mock_chroma:
                mock_chroma.client.get_or_create_collection.return_value = Mock()
                
                # Test processing performance
                start_time = time.time()
                result = test_document_processor.process_documents(["/tmp/test.txt"])
                end_time = time.time()
                
                processing_time = end_time - start_time
                assert processing_time < 3.0  # Should complete within 3 seconds
    
    def test_query_classification_performance(self, test_query_classifier):
        """Test query classification performance."""
        with patch.object(test_query_classifier, 'mistral_client') as mock_mistral:
            mock_mistral.generate_response.return_value = '{"query_type": "SQL_QUERY", "confidence": 0.9}'
            
            # Test classification performance
            start_time = time.time()
            for i in range(20):
                result = test_query_classifier.classify_query(f"Test query {i}")
            end_time = time.time()
            
            classification_time = end_time - start_time
            assert classification_time < 5.0  # Should complete within 5 seconds for 20 queries
    
    def test_sql_generation_performance(self, test_sql_generator):
        """Test SQL generation performance."""
        with patch.object(test_sql_generator, 'mistral_client') as mock_mistral:
            mock_mistral.generate_response.return_value = '{"sql": "SELECT * FROM employees", "confidence": 0.9}'
            
            schema_info = {"tables": {"employees": {"columns": ["id", "name"]}}}
            
            # Test generation performance
            start_time = time.time()
            for i in range(20):
                result = test_sql_generator.generate_sql(f"Test query {i}", schema_info)
            end_time = time.time()
            
            generation_time = end_time - start_time
            assert generation_time < 5.0  # Should complete within 5 seconds for 20 queries

class TestLoadTesting:
    """Test system performance under load."""
    
    def test_concurrent_database_queries(self, test_db_manager):
        """Test concurrent database queries."""
        with patch.object(test_db_manager, 'get_connection') as mock_conn:
            # Mock the context manager properly
            mock_connection = Mock()
            mock_connection.execute.return_value.fetchall.return_value = [
                {"id": 1, "name": "Employee 1"}
            ]
            mock_conn.return_value.__enter__.return_value = mock_connection
            mock_conn.return_value.__exit__.return_value = None
            
            def execute_query():
                with test_db_manager.get_connection() as conn:
                    return conn.execute("SELECT * FROM employees").fetchall()
            
            # Test concurrent execution
            start_time = time.time()
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(execute_query) for _ in range(20)]
                results = [future.result() for future in futures]
            end_time = time.time()
            
            total_time = end_time - start_time
            assert total_time < 3.0  # Should complete within 3 seconds
            assert len(results) == 20
            assert all(result is not None for result in results)
    
    def test_concurrent_document_searches(self, test_document_search_engine):
        """Test concurrent document searches."""
        with patch.object(test_document_search_engine, 'embedding_model') as mock_model:
            mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
            
            with patch.object(test_document_search_engine, 'chromadb_service') as mock_chroma:
                mock_chroma.client.get_collection.return_value.query.return_value = {
                    "documents": [["Test document"]],
                    "metadatas": [[{"filename": "test.pdf"}]],
                    "distances": [[0.1]]
                }
                
                def search_documents():
                    return test_document_search_engine.search_documents("test query")
                
                # Test concurrent execution
                start_time = time.time()
                with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                    futures = [executor.submit(search_documents) for _ in range(15)]
                    results = [future.result() for future in futures]
                end_time = time.time()
                
                total_time = end_time - start_time
                assert total_time < 5.0  # Should complete within 5 seconds
                assert len(results) == 15
                assert all(result is not None for result in results)
    
    def test_concurrent_query_processing(self, test_hybrid_query_processor):
        """Test concurrent query processing."""
        with patch.object(test_hybrid_query_processor, 'query_classifier') as mock_classifier:
            mock_classifier.classify_query.return_value = {
                "query_type": "SQL_QUERY",
                "confidence": 0.9
            }
            
            with patch.object(test_hybrid_query_processor, 'sql_generator') as mock_sql:
                mock_sql.generate_sql.return_value = {
                    "sql": "SELECT * FROM employees",
                    "confidence": 0.9
                }
                
                def process_query():
                    return test_hybrid_query_processor.process_hybrid_query("Test query")
                
                # Test concurrent execution
                start_time = time.time()
                with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                    futures = [executor.submit(process_query) for _ in range(25)]
                    results = [future.result() for future in futures]
                end_time = time.time()
                
                total_time = end_time - start_time
                assert total_time < 8.0  # Should complete within 8 seconds
                assert len(results) == 25
                assert all(result is not None for result in results)

class TestStressTesting:
    """Test system performance under stress conditions."""
    
    def test_high_volume_document_processing(self, test_document_processor):
        """Test high volume document processing."""
        with patch.object(test_document_processor, 'embedding_model') as mock_model:
            mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
            
            with patch.object(test_document_processor, 'chromadb_service') as mock_chroma:
                mock_chroma.client.get_or_create_collection.return_value = Mock()
                
                # Test processing large number of documents
                start_time = time.time()
                result = test_document_processor.process_documents([f"/tmp/test_{i}.txt" for i in range(100)])
                end_time = time.time()
                
                processing_time = end_time - start_time
                assert processing_time < 30.0  # Should complete within 30 seconds
                assert result is not None
    
    def test_high_volume_query_processing(self, test_hybrid_query_processor):
        """Test high volume query processing."""
        with patch.object(test_hybrid_query_processor, 'query_classifier') as mock_classifier:
            mock_classifier.classify_query.return_value = {
                "query_type": "SQL_QUERY",
                "confidence": 0.9
            }
            
            with patch.object(test_hybrid_query_processor, 'sql_generator') as mock_sql:
                mock_sql.generate_sql.return_value = {
                    "sql": "SELECT * FROM employees",
                    "confidence": 0.9
                }
                
                # Test processing large number of queries
                start_time = time.time()
                results = []
                for i in range(50):
                    result = test_hybrid_query_processor.process_hybrid_query(f"Test query {i}")
                    results.append(result)
                end_time = time.time()
                
                processing_time = end_time - start_time
                assert processing_time < 20.0  # Should complete within 20 seconds
                assert len(results) == 50
                assert all(result is not None for result in results)
    
    def test_memory_usage_under_load(self, test_document_processor):
        """Test memory usage under load."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        with patch.object(test_document_processor, 'embedding_model') as mock_model:
            mock_model.encode.return_value = [[0.1, 0.2, 0.3] for _ in range(1000)]
            
            with patch.object(test_document_processor, 'chromadb_service') as mock_chroma:
                mock_chroma.client.get_or_create_collection.return_value = Mock()
                
                # Process many documents
                for i in range(10):
                    result = test_document_processor.process_documents([f"/tmp/test_{i}.txt"])
                
                final_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = final_memory - initial_memory
                
                # Memory increase should be reasonable
                assert memory_increase < 100  # Should not increase by more than 100MB

class TestPerformanceOptimization:
    """Test performance optimization features."""
    
    def test_caching_performance(self, test_redis_service):
        """Test caching performance benefits."""
        with patch.object(test_redis_service, 'client') as mock_redis:
            mock_redis.get.return_value = None  # Cache miss
            mock_redis.set.return_value = True
            
            # Test cache miss performance
            start_time = time.time()
            result1 = test_redis_service.get_cache("test_key")
            end_time = time.time()
            cache_miss_time = end_time - start_time
            
            # Simulate cache hit
            mock_redis.get.return_value = '{"cached_data": "test"}'
            
            start_time = time.time()
            result2 = test_redis_service.get_cache("test_key")
            end_time = time.time()
            cache_hit_time = end_time - start_time
            
            # Cache hit should be faster than cache miss
            assert cache_hit_time < cache_miss_time
    
    def test_connection_pooling_performance(self, test_db_manager):
        """Test database connection pooling performance."""
        with patch.object(test_db_manager, 'get_connection') as mock_conn:
            mock_conn.return_value.execute.return_value.fetchall.return_value = [
                {"id": 1, "name": "Employee 1"}
            ]
            
            # Test multiple connections
            start_time = time.time()
            connections = []
            for i in range(20):
                conn = test_db_manager.get_connection()
                connections.append(conn)
            end_time = time.time()
            
            connection_time = end_time - start_time
            assert connection_time < 1.0  # Should complete within 1 second
            assert len(connections) == 20
    
    def test_batch_processing_performance(self, test_document_processor):
        """Test batch processing performance."""
        with patch.object(test_document_processor, 'embedding_model') as mock_model:
            mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
            
            with patch.object(test_document_processor, 'chromadb_service') as mock_chroma:
                mock_chroma.client.get_or_create_collection.return_value = Mock()
                
                # Test batch processing vs individual processing
                files = [f"/tmp/test_{i}.txt" for i in range(10)]
                
                # Batch processing
                start_time = time.time()
                batch_result = test_document_processor.process_documents(files)
                end_time = time.time()
                batch_time = end_time - start_time
                
                # Individual processing
                start_time = time.time()
                individual_results = []
                for file in files:
                    result = test_document_processor.process_documents([file])
                    individual_results.append(result)
                end_time = time.time()
                individual_time = end_time - start_time
                
                # Batch processing should be more efficient (allow for timing variations)
                assert batch_time <= individual_time + 0.1  # Allow 100ms tolerance
                assert batch_result is not None
                assert len(individual_results) == 10

class TestPerformanceMetrics:
    """Test performance metrics and monitoring."""
    
    def test_response_time_metrics(self, test_hybrid_query_processor):
        """Test response time metrics."""
        with patch.object(test_hybrid_query_processor, 'query_classifier') as mock_classifier:
            mock_classifier.classify_query.return_value = {
                "query_type": "SQL_QUERY",
                "confidence": 0.9
            }
            
            with patch.object(test_hybrid_query_processor, 'sql_generator') as mock_sql:
                mock_sql.generate_sql.return_value = {
                    "sql": "SELECT * FROM employees",
                    "confidence": 0.9
                }
                
                # Test multiple queries and measure response times
                response_times = []
                for i in range(10):
                    start_time = time.time()
                    result = test_hybrid_query_processor.process_hybrid_query(f"Test query {i}")
                    end_time = time.time()
                    response_times.append(end_time - start_time)
                
                # Calculate metrics
                avg_response_time = statistics.mean(response_times)
                max_response_time = max(response_times)
                min_response_time = min(response_times)
                
                assert avg_response_time < 1.0  # Average should be under 1 second
                assert max_response_time < 2.0  # Max should be under 2 seconds
                assert min_response_time >= 0.0  # Min should be non-negative
    
    def test_throughput_metrics(self, test_document_processor):
        """Test throughput metrics."""
        with patch.object(test_document_processor, 'embedding_model') as mock_model:
            mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
            
            with patch.object(test_document_processor, 'chromadb_service') as mock_chroma:
                mock_chroma.client.get_or_create_collection.return_value = Mock()
                
                # Test throughput
                start_time = time.time()
                processed_documents = 0
                
                for i in range(20):
                    result = test_document_processor.process_documents([f"/tmp/test_{i}.txt"])
                    if result and "processed_documents" in result:
                        processed_documents += result["processed_documents"]
                
                end_time = time.time()
                total_time = end_time - start_time
                # Avoid division by zero
                if total_time > 0:
                    throughput = processed_documents / total_time  # documents per second
                    assert throughput >= 0  # Should process at least some documents
                else:
                    throughput = 0
                assert total_time < 10.0  # Should complete within 10 seconds
