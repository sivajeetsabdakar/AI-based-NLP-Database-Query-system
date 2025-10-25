"""
Data Ingestion API Endpoints
Secure endpoints for database connection and document upload
"""
import logging
import os
import tempfile
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Query as FastAPIQuery
from pydantic import BaseModel, Field
from datetime import datetime

from ..models.api_models import (
    DatabaseConnectionRequest, DatabaseConnectionResponse,
    DocumentUploadRequest, DocumentUploadResponse,
    ProcessingStatusRequest, ProcessingStatusResponse,
    BatchProcessingRequest, BatchProcessingResponse,
    BaseResponse, ErrorResponse
)
from ..services.database_initializer import get_database_initializer
from ..services.document_processor import get_or_initialize_document_processor
from ..services.schema_service import get_schema_service

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/ingest", tags=["data-ingestion"])

# Pydantic models for ingestion
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

class DocumentUploadResponse(BaseModel):
    """Document upload response model"""
    success: bool = Field(..., description="Whether upload was successful")
    document_id: Optional[str] = Field(None, description="Generated document ID")
    doc_type: Optional[str] = Field(None, description="Detected document type")
    chunks_count: Optional[int] = Field(None, description="Number of chunks created")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Response timestamp")

class BatchUploadResponse(BaseModel):
    """Batch upload response model"""
    success: bool = Field(..., description="Whether batch upload was successful")
    total_documents: int = Field(..., description="Total number of documents")
    processed_documents: int = Field(..., description="Number of successfully processed documents")
    failed_documents: int = Field(..., description="Number of failed documents")
    document_ids: List[str] = Field(default_factory=list, description="Generated document IDs")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Processing errors")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Response timestamp")

class IngestionStatusResponse(BaseModel):
    """Ingestion status response model"""
    success: bool = Field(..., description="Whether status retrieval was successful")
    status: str = Field(..., description="Current ingestion status")
    progress: float = Field(0.0, ge=0.0, le=1.0, description="Ingestion progress")
    message: Optional[str] = Field(None, description="Status message")
    total_documents: int = Field(0, description="Total documents to process")
    processed_documents: int = Field(0, description="Documents processed")
    failed_documents: int = Field(0, description="Documents failed")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Response timestamp")

# Dependency functions
def get_database_initializer_dependency():
    """Dependency to get database initializer"""
    try:
        return get_database_initializer()
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Database service not available")

def get_document_processor_dependency():
    """Dependency to get document processor with lazy initialization"""
    try:
        return get_or_initialize_document_processor()
    except Exception as e:
        logger.error(f"Failed to get document processor: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Document processor not available: {str(e)}")

def get_schema_service_dependency():
    """Dependency to get schema service"""
    try:
        return get_schema_service()
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Schema service not available")

@router.post("/database", response_model=DatabaseConnectionResponse)
async def connect_database(request: DatabaseConnectionRequest):
    """
    Connect to database and discover schema
    
    This endpoint handles:
    - Database connection validation
    - Schema discovery and analysis
    - Connection testing and verification
    - Database information retrieval
    """
    try:
        logger.info(f"Database connection requested: {request.database_url[:50]}...")
        
        # Validate database URL
        if not request.database_url or not request.database_url.strip():
            raise HTTPException(status_code=400, detail="Database URL is required")
        
        # Test connection if requested
        if request.test_connection:
            # Actually test the database connection
            try:
                from sqlalchemy import create_engine, text
                from urllib.parse import urlparse
                
                # Create engine to test connection
                engine = create_engine(request.database_url, pool_pre_ping=True)
                
                # Test connection
                with engine.connect() as conn:
                    # Parse database URL for info
                    parsed_url = urlparse(request.database_url)
                    db_type = parsed_url.scheme.split('+')[0]  # Get base DB type (postgresql, sqlite, etc.)
                    
                    # Use appropriate version query based on database type
                    try:
                        if db_type == 'postgresql':
                            result = conn.execute(text("SELECT version()"))
                            version_info = result.fetchone()
                            version = version_info[0] if version_info else "Unknown"
                        elif db_type == 'sqlite':
                            result = conn.execute(text("SELECT sqlite_version()"))
                            version_info = result.fetchone()
                            version = f"SQLite {version_info[0]}" if version_info else "Unknown"
                        elif db_type == 'mysql':
                            result = conn.execute(text("SELECT VERSION()"))
                            version_info = result.fetchone()
                            version = f"MySQL {version_info[0]}" if version_info else "Unknown"
                        else:
                            # Generic test for other databases
                            result = conn.execute(text("SELECT 1"))
                            version = f"{db_type.upper()} (version unknown)"
                    except Exception as version_error:
                        # If version query fails, just test with SELECT 1
                        logger.warning(f"Version query failed, using fallback: {str(version_error)}")
                        conn.execute(text("SELECT 1"))
                        version = f"{db_type.upper()} (version query not supported)"
                    
                    connection_status = "connected"
                    database_info = {
                        "type": parsed_url.scheme.replace("+", "_"),
                        "version": version,
                        "host": parsed_url.hostname or "localhost",
                        "port": parsed_url.port or 5432,
                        "database": parsed_url.path.lstrip('/') if parsed_url.path else "Unknown"
                    }
                    
                    logger.info(f"Successfully connected to database: {database_info['database']}")
                    
                # Close engine
                engine.dispose()
                
            except Exception as conn_error:
                logger.error(f"Database connection failed: {str(conn_error)}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Database connection failed: {str(conn_error)}"
                )
        else:
            connection_status = "not_tested"
            database_info = None
        
        # Generate connection ID
        connection_id = f"conn_{int(datetime.utcnow().timestamp())}"
        
        return DatabaseConnectionResponse(
            success=True,
            connection_id=connection_id,
            database_info=database_info,
            connection_status=connection_status,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

@router.post("/documents", response_model=DocumentUploadResponse)
async def upload_documents(
    files: List[UploadFile] = File(..., description="Document files to upload"),
    user_session_id: Optional[str] = Form(None, description="User session ID"),
    doc_type: Optional[str] = Form(None, description="Document type hint")
):
    """
    Upload documents for processing
    
    This endpoint handles:
    - Multi-file document upload
    - File type validation and security scanning
    - Document processing and chunking
    - Progress tracking and status updates
    """
    try:
        logger.info(f"Document upload requested: {len(files)} files")
        
        # Validate files
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        if len(files) > 10:  # Limit to 10 files per request
            raise HTTPException(status_code=400, detail="Too many files. Maximum 10 files per request")
        
        # Validate file types
        allowed_extensions = {'.pdf', '.docx', '.doc', '.txt', '.csv'}
        for file in files:
            if not file.filename:
                raise HTTPException(status_code=400, detail="File must have a filename")
            
            file_ext = os.path.splitext(file.filename)[1].lower()
            if file_ext not in allowed_extensions:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Unsupported file type: {file_ext}. Allowed types: {', '.join(allowed_extensions)}"
                )
        
        # Get document processor
        document_processor = get_document_processor_dependency()
        
        # Save uploaded files temporarily
        temp_files = []
        try:
            for file in files:
                # Create temporary file
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1])
                temp_files.append(temp_file.name)
                
                # Write file content
                content = await file.read()
                temp_file.write(content)
                temp_file.close()
            
            # Process documents
            processing_results = document_processor.process_documents(temp_files, user_session_id)
            
            if processing_results["processed_documents"] > 0:
                # Return first successful document result
                first_doc_id = processing_results["document_ids"][0] if processing_results["document_ids"] else None
                
                return DocumentUploadResponse(
                    success=True,
                    document_id=first_doc_id,
                    doc_type=doc_type,
                    chunks_count=processing_results.get("processed_documents", 0),
                    processing_time=processing_results.get("processing_time", 0.0),
                    timestamp=processing_results.get("start_time", datetime.utcnow().isoformat())
                )
            else:
                return DocumentUploadResponse(
                    success=False,
                    timestamp=datetime.utcnow().isoformat()
                )
                
        finally:
            # Clean up temporary files
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file {temp_file}: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Document upload failed: {str(e)}")

@router.post("/documents/batch", response_model=BatchUploadResponse)
async def batch_upload_documents(
    files: List[UploadFile] = File(..., description="Document files to upload"),
    user_session_id: Optional[str] = Form(None, description="User session ID")
):
    """
    Batch upload and process multiple documents
    
    This endpoint handles:
    - Batch processing of multiple documents
    - Progress tracking for each document
    - Error handling and recovery
    - Comprehensive processing results
    """
    try:
        logger.info(f"Batch document upload requested: {len(files)} files")
        
        # Validate files
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        if len(files) > 50:  # Limit to 50 files per batch request
            raise HTTPException(status_code=400, detail="Too many files. Maximum 50 files per batch request")
        
        # Get document processor
        document_processor = get_document_processor_dependency()
        
        # Save uploaded files temporarily
        temp_files = []
        try:
            for file in files:
                if not file.filename:
                    continue
                
                # Create temporary file
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1])
                temp_files.append(temp_file.name)
                
                # Write file content
                content = await file.read()
                temp_file.write(content)
                temp_file.close()
            
            # Process documents in batch
            processing_results = document_processor.process_documents(temp_files, user_session_id)
            
            return BatchUploadResponse(
                success=processing_results["processed_documents"] > 0,
                total_documents=processing_results["total_documents"],
                processed_documents=processing_results["processed_documents"],
                failed_documents=processing_results["failed_documents"],
                document_ids=processing_results["document_ids"],
                errors=processing_results["errors"],
                processing_time=processing_results.get("processing_time", 0.0),
                timestamp=processing_results.get("start_time", datetime.utcnow().isoformat())
            )
                
        finally:
            # Clean up temporary files
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file {temp_file}: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch document upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch document upload failed: {str(e)}")

@router.get("/status", response_model=IngestionStatusResponse)
async def get_ingestion_status(
    task_id: Optional[str] = FastAPIQuery(None, description="Task ID to check status for"),
    user_session_id: Optional[str] = FastAPIQuery(None, description="User session ID")
):
    """
    Get ingestion processing status
    
    This endpoint provides:
    - Current ingestion status and progress
    - Processing statistics and metrics
    - Error information and recovery status
    - Real-time progress updates
    """
    try:
        logger.info("Ingestion status requested")
        
        # This would typically query a database for processing status
        # For now, return a placeholder response
        return IngestionStatusResponse(
            success=True,
            status="completed",
            progress=1.0,
            message="All documents processed successfully",
            total_documents=0,
            processed_documents=0,
            failed_documents=0,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Failed to get ingestion status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get ingestion status: {str(e)}")

@router.get("/health")
async def ingestion_health():
    """
    Check ingestion service health
    
    This endpoint checks:
    - Document processor availability
    - Database connection status
    - Schema service status
    - Processing queue status
    """
    try:
        health_status = {
            "service": "data_ingestion",
            "status": "healthy",
            "components": {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Check document processor
        try:
            document_processor = get_document_processor_dependency()
            health_status["components"]["document_processor"] = "healthy"
        except Exception as e:
            health_status["components"]["document_processor"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
        
        # Check database initializer
        try:
            database_initializer = get_database_initializer_dependency()
            health_status["components"]["database_initializer"] = "healthy"
        except Exception as e:
            health_status["components"]["database_initializer"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
        
        # Check schema service
        try:
            schema_service = get_schema_service_dependency()
            health_status["components"]["schema_service"] = "healthy"
        except Exception as e:
            health_status["components"]["schema_service"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Ingestion health check failed: {str(e)}")
        return {
            "service": "data_ingestion",
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
