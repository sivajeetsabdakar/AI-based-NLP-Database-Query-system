"""
Unit Tests for Schema Service
Test schema discovery and natural language mapping functionality
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import json

from api.services.schema_service import SchemaService
from api.services.dynamic_schema_discovery import DynamicSchemaDiscovery
from api.services.dynamic_natural_language_mapper import DynamicNaturalLanguageMapper

class TestSchemaService:
    """Test cases for SchemaService."""
    
    def test_schema_service_initialization(self, test_schema_service):
        """Test schema service initialization."""
        assert test_schema_service is not None
        assert hasattr(test_schema_service, 'introspector')
        assert hasattr(test_schema_service, 'mapper')
    
    def test_schema_service_initialize(self, test_schema_service):
        """Test schema service initialization with dependencies."""
        with patch('api.services.schema_service.get_database_utils') as mock_db_utils, \
             patch('api.services.schema_service.get_redis_service') as mock_redis:
            
            mock_db_utils.return_value = Mock()
            mock_redis.return_value = Mock()
            
            result = test_schema_service.initialize()
            assert result is None  # initialize returns None on success
    
    def test_schema_service_initialize_without_dependencies(self, test_schema_service):
        """Test schema service initialization without dependencies."""
        with patch('api.services.schema_service.get_database_utils') as mock_db_utils, \
             patch('api.services.schema_service.get_redis_service') as mock_redis:
            
            mock_db_utils.return_value = None
            mock_redis.return_value = None
            
            # Should not raise exception, just log warning
            result = test_schema_service.initialize()
            assert result is None
    
    def test_get_schema_info(self, test_schema_service, sample_database_schema):
        """Test getting schema information."""
        # Mock discover_schema to return sample schema
        with patch.object(test_schema_service, 'discover_schema') as mock_discover:
            mock_discover.return_value = sample_database_schema
            
            result = test_schema_service.get_schema_info("sqlite:///test.db")
            
            assert result is not None
            assert "tables" in result
            assert "relationships" in result
            mock_discover.assert_called_once_with("sqlite:///test.db")
    
    def test_get_schema_visualization(self, test_schema_service, sample_database_schema):
        """Test getting schema visualization data."""
        # Mock discover_schema to return sample schema
        with patch.object(test_schema_service, 'discover_schema') as mock_discover:
            mock_discover.return_value = sample_database_schema
            
            result = test_schema_service.get_schema_visualization("sqlite:///test.db")
            
            assert result is not None
            assert "nodes" in result
            assert "edges" in result
            # metadata is now part of summary
            mock_discover.assert_called_once_with("sqlite:///test.db")
    
    def test_map_natural_language_to_schema(self, test_schema_service):
        """Test natural language to schema mapping."""
        query = "How many employees do we have?"
        schema_info = {"tables": {"employees": {"columns": ["id", "name"]}}}
        
        with patch.object(test_schema_service, 'mapper') as mock_mapper:
            mock_mapper.map_query_to_schema.return_value = {
                "query_type": "SQL_QUERY",
                "entities": ["employees"],
                "intent": "count"
            }
            
            result = test_schema_service.map_natural_language_to_schema(query, schema_info)
            
            assert result is not None
            assert "query_type" in result
            assert "entities" in result
            mock_mapper.map_query_to_schema.assert_called_once_with(query, schema_info)
    
    def test_refresh_schema(self, test_schema_service, sample_database_schema):
        """Test schema refresh functionality."""
        # Mock discover_schema to return sample schema
        with patch.object(test_schema_service, 'discover_schema') as mock_discover:
            mock_discover.return_value = sample_database_schema
            
            result = test_schema_service.refresh_schema("sqlite:///test.db")
            
            assert result is not None
            assert "tables" in result
            mock_discover.assert_called_once_with("sqlite:///test.db", force_refresh=True)
    
    def test_validate_schema(self, test_schema_service, sample_database_schema):
        """Test schema validation."""
        # Mock discover_schema to return sample schema
        with patch.object(test_schema_service, 'discover_schema') as mock_discover:
            mock_discover.return_value = sample_database_schema
            
            result = test_schema_service.validate_schema("sqlite:///test.db")
            
            assert result is not None
            assert "is_valid" in result  # Changed from "valid" to "is_valid"
            mock_discover.assert_called_once_with("sqlite:///test.db")
    
    def test_export_schema(self, test_schema_service, sample_database_schema):
        """Test schema export functionality."""
        # Mock discover_schema to return sample schema
        with patch.object(test_schema_service, 'discover_schema') as mock_discover:
            mock_discover.return_value = sample_database_schema
            
            result = test_schema_service.export_schema("sqlite:///test.db")
            
            assert result is not None
            assert "tables" in result  # export returns the schema itself
            mock_discover.assert_called_once_with("sqlite:///test.db")

class TestDynamicSchemaDiscovery:
    """Test cases for DynamicSchemaDiscovery."""
    
    def test_dynamic_schema_discovery_initialization(self):
        """Test dynamic schema discovery initialization."""
        discovery = DynamicSchemaDiscovery(connection_string="sqlite:///test.db")
        assert discovery is not None
        assert hasattr(discovery, 'mistral_client')
    
    def test_discover_schema(self, sample_database_schema):
        """Test schema discovery."""
        discovery = DynamicSchemaDiscovery(connection_string="sqlite:///test.db")
        
        with patch.object(discovery, 'mistral_client') as mock_mistral:
            mock_mistral.generate_response.return_value = json.dumps(sample_database_schema)
            
            result = discovery.discover_schema()
            
            assert result is not None
            assert "tables" in result
            assert "relationships" in result
    
    def test_analyze_table_purpose(self, sample_database_schema):
        """Test table purpose analysis."""
        discovery = DynamicSchemaDiscovery(connection_string="sqlite:///test.db")
        table_info = sample_database_schema["tables"]["employees"]
        
        with patch.object(discovery, 'mistral_client') as mock_mistral:
            mock_mistral.generate_response.return_value = "Employee information and management"
            
            result = discovery.analyze_table_purpose("employees", table_info)
            
            assert result is not None
            assert isinstance(result, str)
    
    def test_analyze_column_details(self, sample_database_schema):
        """Test column details analysis."""
        discovery = DynamicSchemaDiscovery(connection_string="sqlite:///test.db")
        columns = sample_database_schema["tables"]["employees"]["columns"]
        
        with patch.object(discovery, 'mistral_client') as mock_mistral:
            mock_mistral.generate_response.return_value = json.dumps({
                "name": "Primary key identifier",
                "email": "Employee email address",
                "salary": "Employee compensation"
            })
            
            result = discovery.analyze_column_details("employees", columns)
            
            assert result is not None
            assert isinstance(result, dict)
    
    def test_detect_relationships(self, sample_database_schema):
        """Test relationship detection."""
        discovery = DynamicSchemaDiscovery(connection_string="sqlite:///test.db")
        
        with patch.object(discovery, 'mistral_client') as mock_mistral:
            mock_mistral.generate_response.return_value = json.dumps(
                sample_database_schema["relationships"]
            )
            
            result = discovery.detect_relationships(sample_database_schema["tables"])
            
            assert result is not None
            assert isinstance(result, list)
    
    def test_validate_schema(self, sample_database_schema):
        """Test schema validation."""
        discovery = DynamicSchemaDiscovery(connection_string="sqlite:///test.db")
        
        with patch.object(discovery, 'mistral_client') as mock_mistral:
            mock_mistral.generate_response.return_value = json.dumps({
                "valid": True,
                "errors": [],
                "warnings": []
            })
            
            result = discovery.validate_schema(sample_database_schema)
            
            assert result is not None
            assert "valid" in result
            assert result["valid"] is True

class TestDynamicNaturalLanguageMapper:
    """Test cases for DynamicNaturalLanguageMapper."""
    
    def test_dynamic_natural_language_mapper_initialization(self):
        """Test dynamic natural language mapper initialization."""
        mapper = DynamicNaturalLanguageMapper()
        assert mapper is not None
        assert hasattr(mapper, 'mistral_client')
    
    def test_map_query_to_schema(self, sample_database_schema):
        """Test query to schema mapping."""
        mapper = DynamicNaturalLanguageMapper()
        query = "How many employees do we have?"
        
        with patch.object(mapper, 'mistral_client') as mock_mistral:
            mock_mistral.generate_response.return_value = json.dumps({
                "query_type": "SQL_QUERY",
                "entities": ["employees"],
                "intent": "count",
                "confidence": 0.9
            })
            
            result = mapper.map_query_to_schema(query, sample_database_schema)
            
            assert result is not None
            assert "query_type" in result
            assert "entities" in result
            assert "intent" in result
    
    def test_extract_entities(self, sample_database_schema):
        """Test entity extraction."""
        mapper = DynamicNaturalLanguageMapper()
        query = "Show me employees in Engineering department"
        
        with patch.object(mapper, 'mistral_client') as mock_mistral:
            mock_mistral.generate_response.return_value = json.dumps({
                "entities": ["employees", "department"],
                "values": ["Engineering"]
            })
            
            result = mapper.extract_entities(query, sample_database_schema)
            
            assert result is not None
            assert "entities" in result
            assert "values" in result
    
    def test_classify_query_intent(self):
        """Test query intent classification."""
        mapper = DynamicNaturalLanguageMapper()
        query = "How many employees do we have?"
        
        with patch.object(mapper, 'mistral_client') as mock_mistral:
            mock_mistral.generate_response.return_value = json.dumps({
                "intent": "count",
                "confidence": 0.9,
                "reasoning": "Query asks for count of employees"
            })
            
            result = mapper.classify_query_intent(query)
            
            assert result is not None
            assert "intent" in result
            assert "confidence" in result
            assert "reasoning" in result
    
    def test_generate_sql_query(self, sample_database_schema):
        """Test SQL query generation."""
        mapper = DynamicNaturalLanguageMapper()
        query = "How many employees do we have?"
        
        with patch.object(mapper, 'mistral_client') as mock_mistral:
            mock_mistral.generate_response.return_value = json.dumps({
                "sql": "SELECT COUNT(*) FROM employees",
                "confidence": 0.9,
                "reasoning": "Count query for employees table"
            })
            
            result = mapper.generate_sql_query(query, sample_database_schema)
            
            assert result is not None
            assert "sql" in result
            assert "confidence" in result
            assert "reasoning" in result
