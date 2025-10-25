"""
API Models
Comprehensive Pydantic models for request/response validation
"""
from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum

# Enums
class QueryType(str, Enum):
    SQL_QUERY = "SQL_QUERY"
    DOCUMENT_QUERY = "DOCUMENT_QUERY"
    HYBRID_QUERY = "HYBRID_QUERY"
    UNKNOWN = "UNKNOWN"

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class DocumentType(str, Enum):
    RESUME = "resume"
    CONTRACT = "contract"
    REVIEW = "review"
    POLICY = "policy"
    GENERAL = "general"

class ComplexityLevel(str, Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"

# Base Models
class BaseResponse(BaseModel):
    """Base response model with common fields"""
    success: bool = Field(..., description="Whether the operation was successful")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Response timestamp")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")

class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = Field(False, description="Always false for errors")
    error: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")

# Query Models
class QueryRequest(BaseModel):
    """Query request model"""
    query: str = Field(..., min_length=1, max_length=1000, description="Natural language query")
    user_context: Optional[Dict[str, Any]] = Field(None, description="Optional user context")
    query_type: Optional[QueryType] = Field(None, description="Optional query type hint")
    
    @validator('query')
    def validate_query(cls, v):
        if not v or not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()

class QueryResponse(BaseModel):
    """Query response model"""
    success: bool = Field(..., description="Whether the query was processed successfully")
    query: str = Field(..., description="Original query")
    query_type: QueryType = Field(..., description="Detected query type")
    results: List[Dict[str, Any]] = Field(default_factory=list, description="Query results")
    total_results: int = Field(0, description="Total number of results")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Query processing confidence")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Response timestamp")

class ClassificationRequest(BaseModel):
    """Query classification request model"""
    query: str = Field(..., min_length=1, max_length=1000, description="Query to classify")
    user_context: Optional[Dict[str, Any]] = Field(None, description="Optional user context")

class ClassificationResponse(BaseModel):
    """Query classification response model"""
    success: bool = Field(..., description="Whether classification was successful")
    query: str = Field(..., description="Original query")
    query_type: QueryType = Field(..., description="Classified query type")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Classification confidence")
    reasoning: str = Field(..., description="Classification reasoning")
    entities: List[str] = Field(default_factory=list, description="Extracted entities")
    intent: str = Field(..., description="Detected user intent")
    complexity: ComplexityLevel = Field(..., description="Query complexity level")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Response timestamp")

# Document Models
class DocumentUploadRequest(BaseModel):
    """Document upload request model"""
    user_session_id: Optional[str] = Field(None, description="User session ID")
    doc_type: Optional[DocumentType] = Field(None, description="Document type hint")
    
class DocumentUploadResponse(BaseModel):
    """Document upload response model"""
    success: bool = Field(..., description="Whether upload was successful")
    document_id: Optional[str] = Field(None, description="Generated document ID")
    doc_type: Optional[DocumentType] = Field(None, description="Detected document type")
    chunks_count: Optional[int] = Field(None, description="Number of chunks created")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Response timestamp")

class DocumentSearchRequest(BaseModel):
    """Document search request model"""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    doc_type: Optional[DocumentType] = Field(None, description="Document type filter")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of results")
    filters: Optional[Dict[str, Any]] = Field(None, description="Optional search filters")

class DocumentSearchResponse(BaseModel):
    """Document search response model"""
    success: bool = Field(..., description="Whether search was successful")
    query: str = Field(..., description="Search query")
    results: List[Dict[str, Any]] = Field(default_factory=list, description="Search results")
    total_results: int = Field(0, description="Total number of results")
    collections_searched: List[str] = Field(default_factory=list, description="Collections searched")
    search_time: str = Field(..., description="Search timestamp")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Response timestamp")

# Schema Models
class SchemaDiscoveryRequest(BaseModel):
    """Schema discovery request model"""
    database_url: str = Field(..., description="Database connection URL")
    refresh_cache: bool = Field(False, description="Whether to refresh cached schema")

class SchemaDiscoveryResponse(BaseModel):
    """Schema discovery response model"""
    success: bool = Field(..., description="Whether discovery was successful")
    schema_info: Dict[str, Any] = Field(..., description="Discovered schema information")
    tables_count: int = Field(0, description="Number of tables discovered")
    relationships_count: int = Field(0, description="Number of relationships discovered")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Response timestamp")

class SchemaVisualizationRequest(BaseModel):
    """Schema visualization request model"""
    include_relationships: bool = Field(True, description="Whether to include relationships")
    include_metadata: bool = Field(True, description="Whether to include metadata")

class SchemaVisualizationResponse(BaseModel):
    """Schema visualization response model"""
    success: bool = Field(..., description="Whether visualization was successful")
    visualization_data: Dict[str, Any] = Field(..., description="Visualization data")
    nodes: List[Dict[str, Any]] = Field(default_factory=list, description="Graph nodes")
    edges: List[Dict[str, Any]] = Field(default_factory=list, description="Graph edges")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Response timestamp")

# Database Models
class DatabaseConnectionRequest(BaseModel):
    """Database connection request model"""
    database_url: str = Field(..., description="Database connection URL")
    connection_name: Optional[str] = Field(None, description="Optional connection name")
    test_connection: bool = Field(True, description="Whether to test the connection")

class DatabaseConnectionResponse(BaseModel):
    """Database connection response model"""
    success: bool = Field(..., description="Whether connection was successful")
    connection_id: Optional[str] = Field(None, description="Generated connection ID")
    database_info: Optional[Dict[str, Any]] = Field(None, description="Database information")
    connection_status: str = Field(..., description="Connection status")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Response timestamp")

# System Models
class HealthCheckResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    uptime: float = Field(..., description="Service uptime in seconds")
    components: Dict[str, str] = Field(..., description="Component status")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Check timestamp")

class SystemStatsResponse(BaseModel):
    """System statistics response model"""
    success: bool = Field(..., description="Whether stats retrieval was successful")
    stats: Dict[str, Any] = Field(..., description="System statistics")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Stats timestamp")

# Processing Models
class ProcessingStatusRequest(BaseModel):
    """Processing status request model"""
    task_id: str = Field(..., description="Task ID to check status for")

class ProcessingStatusResponse(BaseModel):
    """Processing status response model"""
    success: bool = Field(..., description="Whether status retrieval was successful")
    task_id: str = Field(..., description="Task ID")
    status: ProcessingStatus = Field(..., description="Current processing status")
    progress: float = Field(0.0, ge=0.0, le=1.0, description="Processing progress")
    message: Optional[str] = Field(None, description="Status message")
    created_at: Optional[str] = Field(None, description="Task creation timestamp")
    completed_at: Optional[str] = Field(None, description="Task completion timestamp")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Response timestamp")

# Batch Processing Models
class BatchProcessingRequest(BaseModel):
    """Batch processing request model"""
    tasks: List[Dict[str, Any]] = Field(..., min_items=1, max_items=100, description="List of tasks to process")
    user_session_id: Optional[str] = Field(None, description="User session ID")

class BatchProcessingResponse(BaseModel):
    """Batch processing response model"""
    success: bool = Field(..., description="Whether batch processing was successful")
    batch_id: str = Field(..., description="Generated batch ID")
    total_tasks: int = Field(..., description="Total number of tasks")
    queued_tasks: int = Field(..., description="Number of queued tasks")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Response timestamp")

# Analytics Models
class AnalyticsRequest(BaseModel):
    """Analytics request model"""
    start_date: Optional[str] = Field(None, description="Start date for analytics")
    end_date: Optional[str] = Field(None, description="End date for analytics")
    metrics: List[str] = Field(default_factory=list, description="Metrics to include")

class AnalyticsResponse(BaseModel):
    """Analytics response model"""
    success: bool = Field(..., description="Whether analytics retrieval was successful")
    analytics: Dict[str, Any] = Field(..., description="Analytics data")
    period: Dict[str, str] = Field(..., description="Analytics period")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Response timestamp")

# Export Models
class ExportRequest(BaseModel):
    """Export request model"""
    format: str = Field(..., description="Export format (json, csv, xlsx)")
    data_type: str = Field(..., description="Type of data to export")
    filters: Optional[Dict[str, Any]] = Field(None, description="Optional filters")

class ExportResponse(BaseModel):
    """Export response model"""
    success: bool = Field(..., description="Whether export was successful")
    export_id: str = Field(..., description="Generated export ID")
    download_url: Optional[str] = Field(None, description="Download URL for the export")
    file_size: Optional[int] = Field(None, description="Export file size in bytes")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Response timestamp")
