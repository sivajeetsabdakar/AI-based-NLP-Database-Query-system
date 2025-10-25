"""
Query Processing API Endpoints
RESTful API endpoints for query processing and results
"""
import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query as FastAPIQuery
from pydantic import BaseModel, Field
from datetime import datetime

from ..services.query_classifier import get_query_classifier, initialize_query_classifier
from ..services.sql_generator import get_sql_generator, initialize_sql_generator
from ..services.document_search_engine import get_document_search_engine, initialize_document_search_engine
from ..services.hybrid_query_processor import get_hybrid_query_processor, initialize_hybrid_query_processor

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/query", tags=["query-processing"])

# Pydantic models for request/response
class QueryRequest(BaseModel):
    query: str = Field(..., description="Natural language query")
    user_context: Optional[Dict[str, Any]] = Field(None, description="Optional user context")
    query_type: Optional[str] = Field(None, description="Optional query type hint")

class QueryResponse(BaseModel):
    success: bool
    query: str
    query_type: str
    results: List[Dict[str, Any]] = []
    total_results: int = 0
    confidence: float = 0.0
    processing_time: Optional[float] = None
    timestamp: str

class ClassificationRequest(BaseModel):
    query: str = Field(..., description="Query to classify")
    user_context: Optional[Dict[str, Any]] = Field(None, description="Optional user context")

class ClassificationResponse(BaseModel):
    success: bool
    query: str
    query_type: str
    confidence: float
    reasoning: str
    entities: List[str] = []
    intent: str
    complexity: str
    timestamp: str

class SQLGenerationRequest(BaseModel):
    query: str = Field(..., description="Natural language query")
    schema_info: Optional[Dict[str, Any]] = Field(None, description="Optional schema information")
    user_context: Optional[Dict[str, Any]] = Field(None, description="Optional user context")

class SQLGenerationResponse(BaseModel):
    success: bool
    query: str
    sql: str
    confidence: float
    reasoning: str
    tables_used: List[str] = []
    columns_used: List[str] = []
    query_type: str
    security_valid: bool = True
    schema_valid: bool = True
    timestamp: str

class DocumentSearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    doc_type: Optional[str] = Field(None, description="Document type filter")
    limit: int = Field(10, description="Maximum number of results")
    filters: Optional[Dict[str, Any]] = Field(None, description="Optional search filters")

class DocumentSearchResponse(BaseModel):
    success: bool
    query: str
    results: List[Dict[str, Any]] = []
    total_results: int = 0
    collections_searched: List[str] = []
    search_time: str
    timestamp: str

# Dependency functions
def get_query_classifier_dependency():
    """Dependency to get query classifier"""
    try:
        return get_query_classifier()
    except RuntimeError:
        return initialize_query_classifier()

def get_sql_generator_dependency():
    """Dependency to get SQL generator"""
    try:
        return get_sql_generator()
    except RuntimeError:
        return initialize_sql_generator()

def get_document_search_engine_dependency():
    """Dependency to get document search engine"""
    try:
        return get_document_search_engine()
    except RuntimeError:
        return initialize_document_search_engine()

def get_hybrid_query_processor_dependency():
    """Dependency to get hybrid query processor"""
    try:
        return get_hybrid_query_processor()
    except RuntimeError:
        return initialize_hybrid_query_processor()

@router.post("/", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process natural language query using hybrid processing
    
    This endpoint handles:
    - Query classification and routing
    - SQL generation and execution
    - Document search and retrieval
    - Hybrid result combination
    - Intelligent result ranking
    """
    try:
        logger.info(f"Processing query: {request.query[:100]}...")
        
        hybrid_processor = get_hybrid_query_processor_dependency()
        
        # Process hybrid query
        result = hybrid_processor.process_hybrid_query(
            query=request.query,
            user_context=request.user_context
        )
        
        return QueryResponse(
            success=result.get("success", False),
            query=request.query,
            query_type=result.get("query_type", "unknown"),
            results=result.get("results", []),
            total_results=result.get("total_results", 0),
            confidence=result.get("confidence", 0.0),
            processing_time=None,  # Would need to track timing
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Query processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

@router.post("/classify", response_model=ClassificationResponse)
async def classify_query(request: ClassificationRequest):
    """
    Classify natural language query
    
    This endpoint provides:
    - Query type detection (SQL, document, hybrid)
    - Intent analysis and entity extraction
    - Complexity assessment
    - Confidence scoring
    """
    try:
        logger.info(f"Classifying query: {request.query[:100]}...")
        
        classifier = get_query_classifier_dependency()
        classification = classifier.classify_query(
            query=request.query,
            user_context=request.user_context
        )
        
        return ClassificationResponse(
            success=True,
            query=request.query,
            query_type=classification.get("query_type", "unknown"),
            confidence=classification.get("confidence", 0.0),
            reasoning=classification.get("reasoning", ""),
            entities=classification.get("entities", []),
            intent=classification.get("intent", "unknown"),
            complexity=classification.get("complexity", "medium"),
            timestamp=classification.get("timestamp", datetime.utcnow().isoformat())
        )
        
    except Exception as e:
        logger.error(f"Query classification failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Query classification failed: {str(e)}")

@router.post("/sql", response_model=SQLGenerationResponse)
async def generate_sql(request: SQLGenerationRequest):
    """
    Generate SQL from natural language query
    
    This endpoint provides:
    - Natural language to SQL conversion
    - Schema-aware SQL generation
    - SQL validation and security checks
    - Query optimization
    """
    try:
        logger.info(f"Generating SQL for query: {request.query[:100]}...")
        
        sql_generator = get_sql_generator_dependency()
        sql_result = sql_generator.generate_sql(
            query=request.query,
            schema_info=request.schema_info,
            user_context=request.user_context
        )
        
        return SQLGenerationResponse(
            success=bool(sql_result.get("sql")),
            query=request.query,
            sql=sql_result.get("sql", ""),
            confidence=sql_result.get("confidence", 0.0),
            reasoning=sql_result.get("reasoning", ""),
            tables_used=sql_result.get("tables_used", []),
            columns_used=sql_result.get("columns_used", []),
            query_type=sql_result.get("query_type", "SELECT"),
            security_valid=sql_result.get("security_valid", True),
            schema_valid=sql_result.get("schema_valid", True),
            timestamp=sql_result.get("timestamp", datetime.utcnow().isoformat())
        )
        
    except Exception as e:
        logger.error(f"SQL generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"SQL generation failed: {str(e)}")

@router.post("/documents", response_model=DocumentSearchResponse)
async def search_documents(request: DocumentSearchRequest):
    """
    Search documents using vector similarity
    
    This endpoint provides:
    - Vector-based document search
    - Document type filtering
    - Relevance scoring and ranking
    - Metadata and context information
    """
    try:
        logger.info(f"Searching documents for query: {request.query[:100]}...")
        
        search_engine = get_document_search_engine_dependency()
        search_result = search_engine.search_documents(
            query=request.query,
            doc_type=request.doc_type,
            limit=request.limit,
            filters=request.filters
        )
        
        return DocumentSearchResponse(
            success=search_result.get("success", False),
            query=request.query,
            results=search_result.get("results", []),
            total_results=search_result.get("total_results", 0),
            collections_searched=search_result.get("collections_searched", []),
            search_time=search_result.get("search_time", datetime.utcnow().isoformat()),
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Document search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Document search failed: {str(e)}")

@router.get("/history")
async def get_query_history(
    limit: int = FastAPIQuery(10, description="Maximum number of queries to return"),
    offset: int = FastAPIQuery(0, description="Number of queries to skip")
):
    """
    Get query processing history
    
    This endpoint provides:
    - Recent query processing history
    - Query performance metrics
    - Success/failure statistics
    """
    try:
        logger.info("Getting query history")
        
        # This would typically query a database for query history
        # For now, return a placeholder response
        return {
            "success": True,
            "queries": [],
            "total_queries": 0,
            "limit": limit,
            "offset": offset,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get query history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get query history: {str(e)}")

@router.get("/stats")
async def get_query_stats():
    """
    Get query processing statistics
    
    This endpoint provides:
    - Query processing metrics
    - Performance statistics
    - System health information
    """
    try:
        logger.info("Getting query statistics")
        
        # Get stats from various services
        stats = {
            "query_classifier": {},
            "sql_generator": {},
            "document_search": {},
            "hybrid_processor": {}
        }
        
        try:
            classifier = get_query_classifier_dependency()
            stats["query_classifier"] = classifier.get_classification_stats()
        except Exception as e:
            stats["query_classifier"] = {"error": str(e)}
        
        try:
            search_engine = get_document_search_engine_dependency()
            stats["document_search"] = search_engine.get_collection_stats()
        except Exception as e:
            stats["document_search"] = {"error": str(e)}
        
        return {
            "success": True,
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get query stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get query stats: {str(e)}")

@router.get("/health")
async def query_processor_health():
    """
    Check query processor health
    
    This endpoint checks:
    - Query classifier availability
    - SQL generator status
    - Document search engine status
    - Hybrid processor status
    """
    try:
        health_status = {
            "service": "query_processor",
            "status": "healthy",
            "components": {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Check query classifier
        try:
            classifier = get_query_classifier_dependency()
            health_status["components"]["query_classifier"] = "healthy"
        except Exception as e:
            health_status["components"]["query_classifier"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
        
        # Check SQL generator
        try:
            sql_generator = get_sql_generator_dependency()
            health_status["components"]["sql_generator"] = "healthy"
        except Exception as e:
            health_status["components"]["sql_generator"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
        
        # Check document search engine
        try:
            search_engine = get_document_search_engine_dependency()
            health_status["components"]["document_search"] = "healthy"
        except Exception as e:
            health_status["components"]["document_search"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
        
        # Check hybrid processor
        try:
            hybrid_processor = get_hybrid_query_processor_dependency()
            health_status["components"]["hybrid_processor"] = "healthy"
        except Exception as e:
            health_status["components"]["hybrid_processor"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Query processor health check failed: {str(e)}")
        return {
            "service": "query_processor",
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
