"""
Schema Discovery API Endpoints
RESTful API endpoints for schema discovery and natural language mapping
"""
import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel, Field
from ..services.schema_service import get_schema_service, initialize_schema_service
from ..services.database_manager import get_database_manager

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/schema", tags=["schema"])

# Pydantic models for request/response
class DatabaseConnectionRequest(BaseModel):
    connection_string: str = Field(..., description="Database connection string")
    force_refresh: bool = Field(False, description="Force refresh of cached schema")

class QueryMappingRequest(BaseModel):
    query: str = Field(..., description="Natural language query")
    connection_string: str = Field(..., description="Database connection string")

class ColumnSearchRequest(BaseModel):
    term: str = Field(..., description="Search term for column matching")
    connection_string: str = Field(..., description="Database connection string")
    limit: int = Field(10, description="Maximum number of results")

class SchemaValidationRequest(BaseModel):
    connection_string: str = Field(..., description="Database connection string")

class SchemaResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str

class QueryMappingResponse(BaseModel):
    success: bool
    mapping: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    confidence: float = 0.0
    timestamp: str

class ColumnSearchResponse(BaseModel):
    success: bool
    columns: List[Dict[str, Any]] = []
    error: Optional[str] = None
    timestamp: str

class SchemaValidationResponse(BaseModel):
    success: bool
    validation: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str

class SchemaStatisticsResponse(BaseModel):
    success: bool
    statistics: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str

class VisualizationDataResponse(BaseModel):
    success: bool
    visualization_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str

# Dependency to get schema service
def get_schema_service_dependency():
    """Dependency to get schema service"""
    try:
        return get_schema_service()
    except RuntimeError:
        # Initialize if not already initialized
        try:
            return initialize_schema_service()
        except Exception as e:
            logger.error(f"Failed to initialize schema service: {str(e)}")
            raise HTTPException(status_code=503, detail="Schema service not available")

@router.post("/discover", response_model=SchemaResponse)
async def discover_schema(request: DatabaseConnectionRequest):
    """
    Discover database schema
    
    This endpoint performs comprehensive database schema discovery including:
    - Table analysis and purpose detection
    - Column analysis and mapping
    - Relationship detection
    - Schema caching and optimization
    """
    try:
        logger.info(f"Schema discovery requested for connection: {request.connection_string[:50]}...")
        
        schema_service = get_schema_service_dependency()
        schema_data = schema_service.discover_schema(
            connection_string=request.connection_string,
            force_refresh=request.force_refresh
        )
        
        logger.info(f"Schema discovery completed for {schema_data.get('summary', {}).get('total_tables', 0)} tables")
        
        return SchemaResponse(
            success=True,
            data=schema_data,
            timestamp=schema_service._get_timestamp()
        )
        
    except Exception as e:
        logger.error(f"Schema discovery failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Schema discovery failed: {str(e)}")

@router.post("/map-query", response_model=QueryMappingResponse)
async def map_query_to_schema(request: QueryMappingRequest):
    """
    Map natural language query to database schema
    
    This endpoint analyzes a natural language query and maps it to:
    - Relevant database tables
    - Matching columns
    - Query intent detection
    - SQL query suggestions
    """
    try:
        logger.info(f"Query mapping requested: {request.query}")
        
        schema_service = get_schema_service_dependency()
        mapping_result = schema_service.map_query_to_schema(
            query=request.query,
            connection_string=request.connection_string
        )
        
        confidence = mapping_result.get("confidence", 0.0)
        logger.info(f"Query mapping completed with confidence: {confidence:.2f}")
        
        return QueryMappingResponse(
            success=True,
            mapping=mapping_result,
            confidence=confidence,
            timestamp=schema_service._get_timestamp()
        )
        
    except Exception as e:
        logger.error(f"Query mapping failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Query mapping failed: {str(e)}")

@router.post("/search-columns", response_model=ColumnSearchResponse)
async def search_similar_columns(request: ColumnSearchRequest):
    """
    Search for columns similar to a natural language term
    
    This endpoint finds database columns that match or are similar to:
    - Natural language terms
    - Column name patterns
    - Purpose-based matching
    """
    try:
        logger.info(f"Column search requested for term: {request.term}")
        
        schema_service = get_schema_service_dependency()
        similar_columns = schema_service.find_similar_columns(
            term=request.term,
            connection_string=request.connection_string,
            limit=request.limit
        )
        
        logger.info(f"Found {len(similar_columns)} similar columns")
        
        return ColumnSearchResponse(
            success=True,
            columns=similar_columns,
            timestamp=schema_service._get_timestamp()
        )
        
    except Exception as e:
        logger.error(f"Column search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Column search failed: {str(e)}")

@router.post("/validate", response_model=SchemaValidationResponse)
async def validate_schema(request: SchemaValidationRequest):
    """
    Validate discovered schema
    
    This endpoint validates the discovered schema for:
    - Completeness and consistency
    - Relationship integrity
    - Purpose detection accuracy
    - Performance recommendations
    """
    try:
        logger.info(f"Schema validation requested for connection: {request.connection_string[:50]}...")
        
        schema_service = get_schema_service_dependency()
        validation_result = schema_service.validate_schema(
            connection_string=request.connection_string
        )
        
        is_valid = validation_result.get("is_valid", False)
        logger.info(f"Schema validation completed: {'valid' if is_valid else 'invalid'}")
        
        return SchemaValidationResponse(
            success=True,
            validation=validation_result,
            timestamp=schema_service._get_timestamp()
        )
        
    except Exception as e:
        logger.error(f"Schema validation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Schema validation failed: {str(e)}")

@router.get("/statistics")
async def get_schema_statistics(
    connection_string: str = Query(..., description="Database connection string")
):
    """
    Get detailed schema statistics
    
    This endpoint provides comprehensive statistics about the discovered schema:
    - Table and column counts
    - Purpose distribution
    - Column type distribution
    - Schema complexity analysis
    """
    try:
        logger.info(f"Schema statistics requested for connection: {connection_string[:50]}...")
        
        schema_service = get_schema_service_dependency()
        statistics = schema_service.get_schema_statistics(
            connection_string=connection_string
        )
        
        logger.info("Schema statistics retrieved successfully")
        
        return SchemaStatisticsResponse(
            success=True,
            statistics=statistics,
            timestamp=schema_service._get_timestamp()
        )
        
    except Exception as e:
        logger.error(f"Failed to get schema statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get schema statistics: {str(e)}")

@router.get("/summary")
async def get_schema_summary(
    connection_string: str = Query(..., description="Database connection string")
):
    """
    Get schema summary for visualization
    
    This endpoint provides a summary of the schema suitable for:
    - Frontend visualization
    - Schema overview
    - Quick analysis
    """
    try:
        logger.info(f"Schema summary requested for connection: {connection_string[:50]}...")
        
        schema_service = get_schema_service_dependency()
        summary = schema_service.get_schema_summary(
            connection_string=connection_string
        )
        
        logger.info("Schema summary retrieved successfully")
        
        return SchemaResponse(
            success=True,
            data=summary,
            timestamp=schema_service._get_timestamp()
        )
        
    except Exception as e:
        logger.error(f"Failed to get schema summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get schema summary: {str(e)}")

@router.get("/visualization")
async def get_visualization_data(
    connection_string: str = Query(..., description="Database connection string")
):
    """
    Get schema visualization data
    
    This endpoint provides data formatted for frontend visualization:
    - Table nodes with metadata
    - Relationship edges
    - Schema statistics
    - Purpose indicators
    """
    try:
        logger.info(f"Visualization data requested for connection: {connection_string[:50]}...")
        
        schema_service = get_schema_service_dependency()
        visualization_data = schema_service.get_schema_visualization_data(
            connection_string=connection_string
        )
        
        logger.info("Visualization data retrieved successfully")
        
        return VisualizationDataResponse(
            success=True,
            visualization_data=visualization_data,
            timestamp=schema_service._get_timestamp()
        )
        
    except Exception as e:
        logger.error(f"Failed to get visualization data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get visualization data: {str(e)}")

@router.get("/health")
async def schema_service_health():
    """
    Check schema service health
    
    This endpoint checks the health of the schema discovery service:
    - Service availability
    - Dependencies status
    - Performance metrics
    """
    try:
        # Check if schema service is available
        schema_service = get_schema_service_dependency()
        
        # Check database connection
        db_manager = get_database_manager()
        db_status = "healthy" if db_manager else "unhealthy"
        
        health_status = {
            "service": "schema_discovery",
            "status": "healthy",
            "database": db_status,
            "timestamp": schema_service._get_timestamp()
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Schema service health check failed: {str(e)}")
        return {
            "service": "schema_discovery",
            "status": "unhealthy",
            "error": str(e),
            "timestamp": schema_service._get_timestamp() if 'schema_service' in locals() else None
        }

# Add timestamp method to schema service for responses
def _get_timestamp():
    """Get current timestamp"""
    from datetime import datetime
    return datetime.utcnow().isoformat()
