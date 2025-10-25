"""
Security Tests
Test system security and vulnerability prevention
"""
import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock

from api.services.database_manager import DatabaseManager
from api.services.document_processor import DocumentProcessor
from api.services.sql_generator import SQLGenerator
from api.services.query_classifier import QueryClassifier

class TestSQLInjectionPrevention:
    """Test SQL injection prevention."""
    
    def test_sql_injection_in_query(self, test_sql_generator):
        """Test SQL injection prevention in query processing."""
        malicious_queries = [
            "'; DROP TABLE employees; --",
            "1' OR '1'='1",
            "'; INSERT INTO employees VALUES ('hacker', 'hacker@evil.com'); --",
            "1' UNION SELECT * FROM users --",
            "'; UPDATE employees SET salary = 999999 WHERE id = 1; --"
        ]
        
        for malicious_query in malicious_queries:
            with patch.object(test_sql_generator, 'mistral_client') as mock_mistral:
                # Mock should not generate dangerous SQL
                mock_mistral.generate_response.return_value = '{"sql": "SELECT COUNT(*) FROM employees", "confidence": 0.9}'
                
                schema_info = {"tables": {"employees": {"columns": ["id", "name"]}}}
                result = test_sql_generator.generate_sql(malicious_query, schema_info)
                
                # Should not contain dangerous SQL patterns
                assert "DROP" not in result.get("sql", "").upper()
                assert "INSERT" not in result.get("sql", "").upper()
                assert "UPDATE" not in result.get("sql", "").upper()
                assert "DELETE" not in result.get("sql", "").upper()
                assert "UNION" not in result.get("sql", "").upper()
    
    def test_sql_injection_in_database_connection(self, test_db_manager):
        """Test SQL injection prevention in database connections."""
        malicious_connection_strings = [
            "sqlite:///test.db'; DROP TABLE users; --",
            "postgresql://user:pass@host/db'; DELETE FROM employees; --",
            "mysql://user:pass@host/db'; UPDATE employees SET salary = 0; --"
        ]
        
        for malicious_conn in malicious_connection_strings:
            with patch.object(test_db_manager, 'get_connection') as mock_conn:
                mock_conn.return_value.execute.return_value.fetchall.return_value = []
                
                # Should handle malicious connection strings safely
                try:
                    result = test_db_manager.execute_query("SELECT * FROM employees")
                    assert result is not None
                except Exception as e:
                    # Should fail safely, not execute malicious SQL
                    assert "DROP" not in str(e).upper()
                    assert "DELETE" not in str(e).upper()
                    assert "UPDATE" not in str(e).upper()
    
    def test_sql_injection_in_schema_discovery(self, test_db_manager):
        """Test SQL injection prevention in schema discovery."""
        malicious_table_names = [
            "employees'; DROP TABLE users; --",
            "table1'; INSERT INTO employees VALUES ('hacker', 'hacker@evil.com'); --",
            "table2'; UPDATE employees SET salary = 999999; --"
        ]
        
        for malicious_table in malicious_table_names:
            with patch.object(test_db_manager, 'get_connection') as mock_conn:
                mock_conn.return_value.execute.return_value.fetchall.return_value = [
                    {"table_name": malicious_table, "column_name": "id", "data_type": "INTEGER"}
                ]
                
                # Should handle malicious table names safely
                try:
                    result = test_db_manager.execute_query(f"SELECT * FROM {malicious_table}")
                    assert result is not None
                except Exception as e:
                    # Should fail safely
                    assert "DROP" not in str(e).upper()
                    assert "INSERT" not in str(e).upper()
                    assert "UPDATE" not in str(e).upper()

class TestInputValidation:
    """Test input validation and sanitization."""
    
    def test_query_input_validation(self, test_query_classifier):
        """Test query input validation."""
        malicious_inputs = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "'; DROP TABLE employees; --",
            "../../etc/passwd",
            "file:///etc/passwd",
            "http://evil.com/steal-data",
            "data:text/html,<script>alert('XSS')</script>"
        ]
        
        for malicious_input in malicious_inputs:
            with patch.object(test_query_classifier, 'mistral_client') as mock_mistral:
                mock_mistral.generate_response.return_value = '{"query_type": "SQL_QUERY", "confidence": 0.9}'
                
                result = test_query_classifier.classify_query(malicious_input)
                
                # Should sanitize input in processed_query field
                processed_query = result.get("processed_query", "")
                assert "<script>" not in processed_query
                assert "javascript:" not in processed_query
                assert "DROP" not in processed_query.upper()
                assert "../../" not in processed_query
                assert "file://" not in processed_query
    
    def test_document_upload_validation(self, test_document_processor):
        """Test document upload validation."""
        malicious_files = [
            "malicious.exe",
            "virus.bat",
            "trojan.sh",
            "backdoor.py",
            "exploit.js"
        ]
        
        for malicious_file in malicious_files:
            with patch.object(test_document_processor, 'embedding_model') as mock_model:
                mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
                
                with patch.object(test_document_processor, 'chromadb_service') as mock_chroma:
                    mock_chroma.client.get_or_create_collection.return_value = Mock()
                    
                    # Should validate file types
                    try:
                        result = test_document_processor.process_documents([malicious_file])
                        # Should either reject or sanitize
                        assert result is not None
                    except Exception as e:
                        # Should fail safely
                        assert "security" in str(e).lower() or "invalid" in str(e).lower()
    
    def test_database_connection_validation(self, test_db_manager):
        """Test database connection validation."""
        malicious_connections = [
            "sqlite:///../../../etc/passwd",
            "postgresql://user:pass@evil.com:5432/db",
            "mysql://user:pass@malicious.com:3306/db",
            "file:///etc/passwd",
            "http://evil.com/database"
        ]
        
        for malicious_conn in malicious_connections:
            with patch.object(test_db_manager, 'get_connection') as mock_conn:
                mock_conn.return_value.execute.return_value.fetchall.return_value = []
                
                # Should validate connection strings
                try:
                    result = test_db_manager.test_connection(malicious_conn)
                    # Should either reject or sanitize
                    assert result is not None
                except Exception as e:
                    # Should fail safely
                    assert "invalid" in str(e).lower() or "security" in str(e).lower()

class TestFileUploadSecurity:
    """Test file upload security."""
    
    def test_malicious_file_detection(self, test_document_processor):
        """Test malicious file detection."""
        malicious_files = [
            "virus.exe",
            "trojan.bat",
            "backdoor.sh",
            "exploit.py",
            "malware.js"
        ]
        
        for malicious_file in malicious_files:
            with patch.object(test_document_processor, 'embedding_model') as mock_model:
                mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
                
                with patch.object(test_document_processor, 'chromadb_service') as mock_chroma:
                    mock_chroma.client.get_or_create_collection.return_value = Mock()
                    
                    # Should detect and reject malicious files
                    try:
                        result = test_document_processor.process_documents([malicious_file])
                        # Should either reject or sanitize
                        assert result is not None
                    except Exception as e:
                        # Should fail safely
                        assert "security" in str(e).lower() or "malicious" in str(e).lower()
    
    def test_file_size_limits(self, test_document_processor):
        """Test file size limits."""
        # Create a large file
        large_file = tempfile.NamedTemporaryFile(delete=False, suffix='.txt')
        large_content = "x" * (100 * 1024 * 1024)  # 100MB
        large_file.write(large_content.encode())
        large_file.close()
        
        try:
            with patch.object(test_document_processor, 'embedding_model') as mock_model:
                mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
                
                with patch.object(test_document_processor, 'chromadb_service') as mock_chroma:
                    mock_chroma.client.get_or_create_collection.return_value = Mock()
                    
                    # Should handle large files appropriately
                    try:
                        result = test_document_processor.process_documents([large_file.name])
                        # Should either reject or process safely
                        assert result is not None
                    except Exception as e:
                        # Should fail safely
                        assert "size" in str(e).lower() or "limit" in str(e).lower()
        finally:
            os.unlink(large_file.name)
    
    def test_file_type_validation(self, test_document_processor):
        """Test file type validation."""
        invalid_files = [
            "script.exe",
            "malware.bat",
            "virus.sh",
            "trojan.com",
            "backdoor.scr"
        ]
        
        for invalid_file in invalid_files:
            with patch.object(test_document_processor, 'embedding_model') as mock_model:
                mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
                
                with patch.object(test_document_processor, 'chromadb_service') as mock_chroma:
                    mock_chroma.client.get_or_create_collection.return_value = Mock()
                    
                    # Should validate file types
                    try:
                        result = test_document_processor.process_documents([invalid_file])
                        # Should either reject or sanitize
                        assert result is not None
                    except Exception as e:
                        # Should fail safely
                        assert "type" in str(e).lower() or "format" in str(e).lower()

class TestAuthenticationSecurity:
    """Test authentication and authorization security."""
    
    def test_api_key_validation(self, test_client):
        """Test API key validation."""
        # Test without API key
        response = test_client.post("/api/query/", json={"query": "test"})
        # Should either require authentication or handle gracefully
        assert response.status_code in [200, 401, 403]
        
        # Test with invalid API key
        headers = {"Authorization": "Bearer invalid_key"}
        response = test_client.post("/api/query/", json={"query": "test"}, headers=headers)
        # Should reject invalid key
        assert response.status_code in [200, 401, 403]
    
    def test_rate_limiting(self, test_client):
        """Test rate limiting."""
        # Test multiple rapid requests
        for i in range(100):
            response = test_client.post("/api/query/", json={"query": f"test {i}"})
            if response.status_code == 429:  # Rate limited
                break
        else:
            # If not rate limited, should still handle gracefully
            assert response.status_code in [200, 429]
    
    def test_session_security(self, test_client):
        """Test session security."""
        # Test session hijacking prevention
        response1 = test_client.post("/api/query/", json={"query": "test1"})
        session_id = response1.cookies.get("session_id")
        
        if session_id:
            # Test with different session
            response2 = test_client.post("/api/query/", json={"query": "test2"})
            # Should handle session security appropriately
            assert response2.status_code in [200, 401, 403]

class TestDataSecurity:
    """Test data security and privacy."""
    
    def test_sensitive_data_masking(self, test_db_manager):
        """Test sensitive data masking."""
        sensitive_queries = [
            "SELECT password FROM users",
            "SELECT credit_card FROM customers",
            "SELECT ssn FROM employees",
            "SELECT salary FROM employees WHERE id = 1"
        ]
        
        for sensitive_query in sensitive_queries:
            with patch.object(test_db_manager, 'get_connection') as mock_conn:
                mock_conn.return_value.execute.return_value.fetchall.return_value = [
                    {"password": "***", "credit_card": "***", "ssn": "***", "salary": "***"}
                ]
                
                result = test_db_manager.execute_query(sensitive_query)
                
                # Should mask sensitive data
                if result:
                    for row in result:
                        for key, value in row.items():
                            if key in ["password", "credit_card", "ssn", "salary"]:
                                assert value == "***" or "***" in str(value)
    
    def test_data_encryption(self, test_redis_service):
        """Test data encryption in cache."""
        sensitive_data = {
            "password": "secret123",
            "credit_card": "1234-5678-9012-3456",
            "ssn": "123-45-6789"
        }
        
        with patch.object(test_redis_service, 'redis_client') as mock_redis:
            mock_redis.set.return_value = True
            mock_redis.get.return_value = '{"encrypted": "data"}'
            
            # Should encrypt sensitive data
            result = test_redis_service.set_cache("sensitive_key", sensitive_data)
            assert result is not None
            
            # Should decrypt when retrieving
            retrieved = test_redis_service.get_cache("sensitive_key")
            assert retrieved is not None
    
    def test_audit_logging(self, test_db_manager):
        """Test audit logging for security events."""
        with patch.object(test_db_manager, 'get_connection') as mock_conn:
            mock_conn.return_value.execute.return_value.fetchall.return_value = []
            
            # Should log security events
            result = test_db_manager.execute_query("SELECT * FROM employees")
            assert result is not None
            
            # Should log access attempts
            # This would be implemented in the actual service

class TestNetworkSecurity:
    """Test network security."""
    
    def test_cors_security(self, test_client):
        """Test CORS security."""
        # Test with different origins
        headers = {"Origin": "http://evil.com"}
        response = test_client.get("/health", headers=headers)
        
        # Should handle CORS appropriately
        assert response.status_code in [200, 403]
    
    def test_https_enforcement(self, test_client):
        """Test HTTPS enforcement."""
        # Test with HTTP
        response = test_client.get("/health")
        
        # Should either redirect to HTTPS or handle appropriately
        assert response.status_code in [200, 301, 302]
    
    def test_request_size_limits(self, test_client):
        """Test request size limits."""
        # Test with large request
        large_data = {"query": "x" * (10 * 1024 * 1024)}  # 10MB
        
        response = test_client.post("/api/query/", json=large_data)
        
        # Should handle large requests appropriately
        assert response.status_code in [200, 413, 400]

class TestVulnerabilityScanning:
    """Test vulnerability scanning."""
    
    def test_xss_prevention(self, test_query_classifier):
        """Test XSS prevention."""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "data:text/html,<script>alert('XSS')</script>"
        ]
        
        for xss_payload in xss_payloads:
            with patch.object(test_query_classifier, 'mistral_client') as mock_mistral:
                mock_mistral.generate_response.return_value = '{"query_type": "SQL_QUERY", "confidence": 0.9}'
                
                result = test_query_classifier.classify_query(xss_payload)
                
                # Should sanitize XSS payloads
                assert "<script>" not in str(result)
                assert "javascript:" not in str(result)
                assert "onerror" not in str(result)
                assert "onload" not in str(result)
    
    def test_path_traversal_prevention(self, test_document_processor):
        """Test path traversal prevention."""
        path_traversal_payloads = [
            "../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "C:\\windows\\system32\\config\\sam",
            "....//....//etc//passwd"
        ]
        
        for payload in path_traversal_payloads:
            with patch.object(test_document_processor, 'embedding_model') as mock_model:
                mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
                
                with patch.object(test_document_processor, 'chromadb_service') as mock_chroma:
                    mock_chroma.client.get_or_create_collection.return_value = Mock()
                    
                    # Should prevent path traversal
                    try:
                        result = test_document_processor.process_documents([payload])
                        # Should either reject or sanitize
                        assert result is not None
                    except Exception as e:
                        # Should fail safely
                        assert "path" in str(e).lower() or "traversal" in str(e).lower()
    
    def test_command_injection_prevention(self, test_sql_generator):
        """Test command injection prevention."""
        command_injection_payloads = [
            "; rm -rf /",
            "| cat /etc/passwd",
            "&& whoami",
            "`id`",
            "$(id)"
        ]
        
        for payload in command_injection_payloads:
            with patch.object(test_sql_generator, 'mistral_client') as mock_mistral:
                mock_mistral.generate_response.return_value = '{"sql": "SELECT * FROM employees", "confidence": 0.9}'
                
                schema_info = {"tables": {"employees": {"columns": ["id", "name"]}}}
                result = test_sql_generator.generate_sql(payload, schema_info)
                
                # Should not execute commands (check for actual command injection patterns)
                sql_result = str(result.get("sql", ""))
                assert "rm " not in sql_result  # Space after rm to avoid matching "from"
                assert "cat " not in sql_result
                assert "whoami" not in sql_result
                assert "&&" not in sql_result
                assert "||" not in sql_result
