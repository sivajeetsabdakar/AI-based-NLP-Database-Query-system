"""
Schema Discovery Service
Main service that orchestrates schema discovery and natural language mapping
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from .dynamic_schema_discovery import DynamicSchemaDiscovery
from .dynamic_natural_language_mapper import DynamicNaturalLanguageMapper
from .database_utils import get_database_utils
from .redis_service import get_redis_service

logger = logging.getLogger(__name__)

class SchemaService:
    """Main service for schema discovery and natural language mapping"""
    
    def __init__(self):
        self.logger = logger
        self.introspector = None
        self.mapper = DynamicNaturalLanguageMapper()
        self.db_utils = None
        self.redis_service = None
        
    def initialize(self):
        """Initialize the schema service"""
        try:
            # Initialize database utils and redis service
            from .database_utils import get_database_utils
            from .redis_service import get_redis_service
            
            self.db_utils = get_database_utils()
            self.redis_service = get_redis_service()
            self.logger.info("Schema service initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize schema service: {str(e)}")
            # Don't raise the exception, just log it - service can still work without these dependencies
            self.logger.warning("Schema service initialized with limited functionality")
    
    def discover_schema(self, connection_string: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Discover database schema with caching
        
        Args:
            connection_string: Database connection string
            force_refresh: Force refresh of cached schema
            
        Returns:
            Complete schema information
        """
        try:
            # Check cache first
            if not force_refresh:
                cached_schema = self._get_cached_schema(connection_string)
                if cached_schema:
                    self.logger.info("Returning cached schema")
                    return cached_schema
            
            # Initialize dynamic schema discovery
            self.introspector = DynamicSchemaDiscovery(connection_string)
            self.introspector.initialize()
            
            # Discover schema
            self.logger.info("Starting schema discovery...")
            schema = self.introspector.discover_schema()
            
            # Cache the schema
            self._cache_schema(connection_string, schema)
            
            # Log schema discovery
            self._log_schema_discovery(connection_string, schema)
            
            self.logger.info(f"Schema discovery completed for {schema.get('summary', {}).get('total_tables', 0)} tables")
            return schema
            
        except Exception as e:
            self.logger.error(f"Schema discovery failed: {str(e)}")
            raise
        finally:
            if self.introspector:
                self.introspector.close()
    
    def map_query_to_schema(self, query: str, connection_string: str) -> Dict[str, Any]:
        """
        Map natural language query to database schema
        
        Args:
            query: Natural language query
            connection_string: Database connection string
            
        Returns:
            Mapping results
        """
        try:
            # Get schema (from cache or discover)
            schema = self.discover_schema(connection_string)
            
            # Map query to schema
            mapping_result = self.mapper.map_query_to_schema(query, schema)
            
            # Log the mapping
            self._log_query_mapping(query, mapping_result)
            
            return mapping_result
            
        except Exception as e:
            self.logger.error(f"Query mapping failed: {str(e)}")
            return {
                "query": query,
                "error": str(e),
                "confidence": 0.0
            }
    
    def get_schema_summary(self, connection_string: str) -> Dict[str, Any]:
        """Get schema summary for visualization"""
        try:
            schema = self.discover_schema(connection_string)
            return self.mapper.get_schema_summary(schema)
            
        except Exception as e:
            self.logger.error(f"Failed to get schema summary: {str(e)}")
            return {"error": str(e)}
    
    def find_similar_columns(self, term: str, connection_string: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Find columns similar to a natural language term"""
        try:
            schema = self.discover_schema(connection_string)
            similar_columns = self.mapper.find_similar_columns(term, schema, limit)
            
            # Format results
            results = []
            for table_name, column_name, similarity in similar_columns:
                results.append({
                    "table_name": table_name,
                    "column_name": column_name,
                    "similarity_score": similarity
                })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to find similar columns: {str(e)}")
            return []
    
    def validate_schema(self, connection_string: str) -> Dict[str, Any]:
        """Validate discovered schema"""
        try:
            schema = self.discover_schema(connection_string)
            
            validation_results = {
                "is_valid": True,
                "errors": [],
                "warnings": [],
                "recommendations": []
            }
            
            # Validate tables
            tables = schema.get("tables", {})
            if not tables:
                validation_results["errors"].append("No tables found in database")
                validation_results["is_valid"] = False
            
            # Check for tables without primary keys
            for table_name, table_info in tables.items():
                constraints = table_info.get("constraints", {})
                if not constraints.get("primary_keys", {}).get("constrained_columns"):
                    validation_results["warnings"].append(f"Table '{table_name}' has no primary key")
            
            # Check for tables without relationships
            relationships = schema.get("relationships", [])
            if len(relationships) == 0:
                validation_results["warnings"].append("No relationships detected between tables")
            
            # Check for tables with low purpose confidence
            for table_name, table_info in tables.items():
                purpose = table_info.get("purpose", {})
                if purpose.get("confidence", 0) < 0.5:
                    validation_results["recommendations"].append(
                        f"Table '{table_name}' purpose detection has low confidence ({purpose.get('confidence', 0):.2f})"
                    )
            
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Schema validation failed: {str(e)}")
            return {
                "is_valid": False,
                "errors": [str(e)],
                "warnings": [],
                "recommendations": []
            }
    
    def get_schema_statistics(self, connection_string: str) -> Dict[str, Any]:
        """Get detailed schema statistics"""
        try:
            schema = self.discover_schema(connection_string)
            summary = schema.get("summary", {})
            
            # Calculate additional statistics
            tables = schema.get("tables", {})
            total_columns = sum(len(table.get("columns", {})) for table in tables.values())
            
            # Purpose distribution
            purpose_distribution = {}
            for table_info in tables.values():
                purpose = table_info.get("purpose", {}).get("primary_purpose", "unknown")
                purpose_distribution[purpose] = purpose_distribution.get(purpose, 0) + 1
            
            # Column type distribution
            column_types = {}
            for table_info in tables.values():
                for col_info in table_info.get("columns", {}).values():
                    col_type = str(col_info.get("type", ""))
                    column_types[col_type] = column_types.get(col_type, 0) + 1
            
            return {
                "total_tables": summary.get("total_tables", 0),
                "total_columns": total_columns,
                "total_relationships": summary.get("total_relationships", 0),
                "average_columns_per_table": summary.get("average_columns_per_table", 0),
                "purpose_distribution": purpose_distribution,
                "column_type_distribution": dict(sorted(column_types.items(), key=lambda x: x[1], reverse=True)[:10]),
                "schema_complexity": self._calculate_complexity_score(tables, schema.get("relationships", [])),
                "discovery_timestamp": schema.get("discovered_at")
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get schema statistics: {str(e)}")
            return {"error": str(e)}
    
    def _get_cached_schema(self, connection_string: str) -> Optional[Dict[str, Any]]:
        """Get cached schema if available and not expired"""
        try:
            if self.db_utils:
                return self.db_utils.get_cached_schema_data(connection_string)
            return None
        except Exception as e:
            self.logger.warning(f"Failed to get cached schema: {str(e)}")
            return None
    
    def _cache_schema(self, connection_string: str, schema: Dict[str, Any]):
        """Cache discovered schema"""
        try:
            if self.db_utils:
                # Cache in database
                from .database_manager import get_database_manager
                db_manager = get_database_manager()
                with db_manager.get_session() as session:
                    self.db_utils.cache_schema_data(session, connection_string, schema, ttl_hours=24)
            
            if self.redis_service:
                # Also cache in Redis
                connection_hash = self._generate_connection_hash(connection_string)
                self.redis_service.cache_schema_data(connection_hash, schema, 86400)  # 24 hours
            
        except Exception as e:
            self.logger.warning(f"Failed to cache schema: {str(e)}")
    
    def _log_schema_discovery(self, connection_string: str, schema: Dict[str, Any]):
        """Log schema discovery for analytics"""
        try:
            from .database_manager import get_database_manager
            db_manager = get_database_manager()
            with db_manager.get_session() as session:
                # Log as a system event
                from ..models.database_models import SystemLog
                log_entry = SystemLog(
                    level="INFO",
                    logger_name="schema_discovery",
                    message=f"Schema discovery completed for {schema.get('summary', {}).get('total_tables', 0)} tables",
                    module="schema_service",
                    function="discover_schema"
                )
                session.add(log_entry)
                session.commit()
                
        except Exception as e:
            self.logger.warning(f"Failed to log schema discovery: {str(e)}")
    
    def _log_query_mapping(self, query: str, mapping_result: Dict[str, Any]):
        """Log query mapping for analytics"""
        try:
            from .database_manager import get_database_manager
            db_manager = get_database_manager()
            with db_manager.get_session() as session:
                # Log as a system event
                from ..models.database_models import SystemLog
                confidence = mapping_result.get("confidence", 0.0)
                log_entry = SystemLog(
                    level="INFO",
                    logger_name="query_mapping",
                    message=f"Query mapped with confidence {confidence:.2f}: {query[:100]}",
                    module="schema_service",
                    function="map_query_to_schema"
                )
                session.add(log_entry)
                session.commit()
                
        except Exception as e:
            self.logger.warning(f"Failed to log query mapping: {str(e)}")
    
    def _calculate_complexity_score(self, tables: Dict, relationships: List) -> str:
        """Calculate schema complexity score"""
        total_tables = len(tables)
        total_relationships = len(relationships)
        
        # Calculate average columns per table
        total_columns = sum(len(table.get("columns", {})) for table in tables.values())
        avg_columns = total_columns / total_tables if total_tables > 0 else 0
        
        # Calculate complexity score
        complexity_score = (total_tables * 0.3 + total_relationships * 0.4 + avg_columns * 0.3)
        
        if complexity_score < 10:
            return "simple"
        elif complexity_score < 30:
            return "moderate"
        else:
            return "complex"
    
    def _generate_connection_hash(self, connection_string: str) -> str:
        """Generate hash for connection string"""
        import hashlib
        return hashlib.sha256(connection_string.encode()).hexdigest()
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    def get_schema_visualization_data(self, connection_string: str) -> Dict[str, Any]:
        """Get data for frontend schema visualization"""
        try:
            schema = self.discover_schema(connection_string)
            
            # Prepare visualization data
            tables = schema.get("tables", {})
            relationships = schema.get("relationships", [])
            
            # Format tables for visualization
            table_nodes = []
            for table_name, table_info in tables.items():
                purpose = table_info.get("purpose", {}).get("primary_purpose", "unknown")
                confidence = table_info.get("purpose", {}).get("confidence", 0.0)
                
                table_nodes.append({
                    "id": table_name,
                    "name": table_name,
                    "purpose": purpose,
                    "confidence": confidence,
                    "columns": list(table_info.get("columns", {}).keys()),
                    "row_count": table_info.get("row_count", 0),
                    "size": table_info.get("size_estimate", "Unknown")
                })
            
            # Format relationships for visualization
            relationship_edges = []
            for rel in relationships:
                relationship_edges.append({
                    "source": rel.get("source_table"),
                    "target": rel.get("target_table"),
                    "type": rel.get("type"),
                    "confidence": rel.get("confidence", 0.0),
                    "source_columns": rel.get("source_columns", []),
                    "target_columns": rel.get("target_columns", [])
                })
            
            return {
                "nodes": table_nodes,
                "edges": relationship_edges,
                "summary": schema.get("summary", {}),
                "statistics": self.get_schema_statistics(connection_string)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get visualization data: {str(e)}")
            return {"error": str(e)}
    
    # Wrapper methods for backward compatibility with tests
    def get_schema_info(self, connection_string: str = None) -> Dict[str, Any]:
        """Wrapper for discover_schema (backward compatibility)"""
        if connection_string is None:
            return {"error": "connection_string is required"}
        return self.discover_schema(connection_string)
    
    def get_schema_visualization(self, connection_string: str = None) -> Dict[str, Any]:
        """Wrapper for get_schema_visualization_data (backward compatibility)"""
        if connection_string is None:
            return {"error": "connection_string is required"}
        return self.get_schema_visualization_data(connection_string)
    
    def map_natural_language_to_schema(self, query: str, schema_info: Dict[str, Any]) -> Dict[str, Any]:
        """Wrapper for mapper.map_query_to_schema (backward compatibility)"""
        return self.mapper.map_query_to_schema(query, schema_info)
    
    def refresh_schema(self, connection_string: str = None) -> Dict[str, Any]:
        """Wrapper for discover_schema with force_refresh (backward compatibility)"""
        if connection_string is None:
            return {"error": "connection_string is required"}
        return self.discover_schema(connection_string, force_refresh=True)
    
    def export_schema(self, connection_string: str = None, format: str = "json") -> Dict[str, Any]:
        """Export schema in specified format (backward compatibility)"""
        if connection_string is None:
            return {"error": "connection_string is required"}
        
        schema = self.discover_schema(connection_string)
        
        if format == "json":
            return schema
        elif format == "summary":
            return self.get_schema_summary(connection_string)
        else:
            return {"error": f"Unsupported export format: {format}"}

# Global schema service instance
schema_service: Optional[SchemaService] = None

def get_schema_service() -> SchemaService:
    """Get the global schema service instance"""
    if schema_service is None:
        raise RuntimeError("Schema service not initialized")
    return schema_service

def initialize_schema_service() -> SchemaService:
    """Initialize the global schema service"""
    global schema_service
    schema_service = SchemaService()
    schema_service.initialize()
    return schema_service
