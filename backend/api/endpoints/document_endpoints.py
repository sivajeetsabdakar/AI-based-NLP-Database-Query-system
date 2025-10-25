"""
Document Processing API Endpoints
RESTful API endpoints for document upload, processing, and retrieval
"""
import logging
import os
import tempfile
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Query
from pydantic import BaseModel, Field
from ..services.document_processor import get_document_processor, initialize_document_processor
from ..services.database_manager import get_database_manager

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/ingest", tags=["document-processing"])

# Pydantic models for request/response
class DocumentUploadRequest(BaseModel):
    user_session_id: Optional[str] = Field(None, description="User session ID")
    doc_type: Optional[str] = Field(None, description="Document type hint")

class DocumentProcessingResponse(BaseModel):
    success: bool
    document_id: Optional[str] = None
    doc_type: Optional[str] = None
    chunks_count: Optional[int] = None
    processing_time: Optional[float] = None
    error: Optional[str] = None
    timestamp: str

class BatchProcessingResponse(BaseModel):
    success: bool
    total_documents: int
    processed_documents: int
    failed_documents: int
    document_ids: List[str] = []
    errors: List[Dict[str, Any]] = []
    processing_time: Optional[float] = None
    timestamp: str

class DocumentSearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    doc_type: Optional[str] = Field(None, description="Document type filter")
    limit: int = Field(10, description="Maximum number of results")

class DocumentSearchResponse(BaseModel):
    success: bool
    results: List[Dict[str, Any]] = []
    total_results: int = 0
    query: str
    timestamp: str

class ProcessingStatusResponse(BaseModel):
    success: bool
    status: str
    document_id: Optional[str] = None
    filename: Optional[str] = None
    file_type: Optional[str] = None
    processing_status: Optional[str] = None
    created_at: Optional[str] = None
    error: Optional[str] = None
    timestamp: str

# Dependency to get document processor
def get_document_processor_dependency():
    """Dependency to get document processor"""
    try:
        return get_document_processor()
    except RuntimeError:
        # Initialize if not already initialized
        return initialize_document_processor()

@router.post("/documents", response_model=DocumentProcessingResponse)
async def upload_documents(
    files: List[UploadFile] = File(..., description="Document files to upload"),
    user_session_id: Optional[str] = Form(None, description="User session ID"),
    doc_type: Optional[str] = Form(None, description="Document type hint")
):
    """
    Upload and process multiple documents
    
    This endpoint handles:
    - Multiple file uploads (PDF, DOCX, TXT, CSV)
    - Automatic format detection
    - Intelligent chunking based on document type
    - Embedding generation and ChromaDB storage
    - Progress tracking and status updates
    """
    try:
        logger.info(f"Document upload requested: {len(files)} files")
        
        document_processor = get_document_processor_dependency()
        
        # Save uploaded files temporarily
        temp_files = []
        try:
            for file in files:
                # Validate file type
                if not file.filename:
                    raise HTTPException(status_code=400, detail="File must have a filename")
                
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
                
                return DocumentProcessingResponse(
                    success=True,
                    document_id=first_doc_id,
                    doc_type=doc_type,
                    chunks_count=processing_results.get("processed_documents", 0),
                    processing_time=processing_results.get("processing_time", 0.0),
                    timestamp=processing_results.get("start_time", "")
                )
            else:
                return DocumentProcessingResponse(
                    success=False,
                    error="No documents were processed successfully",
                    timestamp=processing_results.get("start_time", "")
                )
                
        finally:
            # Clean up temporary files
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file {temp_file}: {str(e)}")
        
    except Exception as e:
        logger.error(f"Document upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Document upload failed: {str(e)}")

@router.post("/documents/batch", response_model=BatchProcessingResponse)
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
            
            return BatchProcessingResponse(
                success=processing_results["processed_documents"] > 0,
                total_documents=processing_results["total_documents"],
                processed_documents=processing_results["processed_documents"],
                failed_documents=processing_results["failed_documents"],
                document_ids=processing_results["document_ids"],
                errors=processing_results["errors"],
                processing_time=processing_results.get("processing_time", 0.0),
                timestamp=processing_results.get("start_time", "")
            )
                
        finally:
            # Clean up temporary files
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file {temp_file}: {str(e)}")
        
    except Exception as e:
        logger.error(f"Batch document upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch document upload failed: {str(e)}")

@router.get("/status/{document_id}")
async def get_processing_status(document_id: str):
    """
    Get processing status for a specific document
    
    This endpoint provides:
    - Document processing status
    - File information and metadata
    - Processing timestamps
    - Error information if processing failed
    """
    try:
        logger.info(f"Processing status requested for document: {document_id}")
        
        document_processor = get_document_processor_dependency()
        status = document_processor.get_processing_status(document_id)
        
        return ProcessingStatusResponse(
            success=status.get("status") != "error",
            status=status.get("status", "unknown"),
            document_id=status.get("document_id"),
            filename=status.get("filename"),
            file_type=status.get("file_type"),
            processing_status=status.get("processing_status"),
            created_at=status.get("created_at"),
            error=status.get("error"),
            timestamp=status.get("created_at", "")
        )
        
    except Exception as e:
        logger.error(f"Failed to get processing status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get processing status: {str(e)}")

@router.post("/search", response_model=DocumentSearchResponse)
async def search_documents(request: DocumentSearchRequest):
    """
    Search documents using vector similarity
    
    This endpoint provides:
    - Vector similarity search across all document types
    - Document type filtering
    - Relevance scoring and ranking
    - Metadata and context information
    """
    try:
        logger.info(f"Document search requested: {request.query}")
        
        document_processor = get_document_processor_dependency()
        results = document_processor.search_documents(
            query=request.query,
            doc_type=request.doc_type,
            limit=request.limit
        )
        
        return DocumentSearchResponse(
            success=True,
            results=results,
            total_results=len(results),
            query=request.query,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Document search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Document search failed: {str(e)}")

@router.get("/collections")
async def get_collections():
    """
    Get available document collections
    
    This endpoint provides:
    - List of available ChromaDB collections
    - Collection statistics and metadata
    - Document counts per collection
    """
    try:
        logger.info("Collections information requested")
        
        document_processor = get_document_processor_dependency()
        
        if not document_processor.chromadb_service or not document_processor.chromadb_service.client:
            raise HTTPException(status_code=503, detail="ChromaDB service not available")
        
        collections_info = []
        collection_names = [
            "employee_documents",
            "resume_chunks",
            "contract_chunks", 
            "review_chunks",
            "policy_chunks"
        ]
        
        for collection_name in collection_names:
            try:
                collection = document_processor.chromadb_service.client.get_collection(collection_name)
                count = collection.count()
                
                collections_info.append({
                    "name": collection_name,
                    "count": count,
                    "type": "document" if collection_name == "employee_documents" else "chunk"
                })
            except Exception as e:
                logger.warning(f"Failed to get collection {collection_name}: {str(e)}")
                collections_info.append({
                    "name": collection_name,
                    "count": 0,
                    "type": "document" if collection_name == "employee_documents" else "chunk",
                    "error": str(e)
                })
        
        return {
            "success": True,
            "collections": collections_info,
            "total_collections": len(collections_info),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get collections: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get collections: {str(e)}")

@router.get("/health")
async def document_processor_health():
    """
    Check document processor health
    
    This endpoint checks:
    - Document processor availability
    - ChromaDB connection status
    - Embedding model status
    - Database connection status
    """
    try:
        # Check if document processor is available
        document_processor = get_document_processor_dependency()
        
        # Check ChromaDB connection
        chromadb_status = "healthy" if document_processor.chromadb_service else "unhealthy"
        
        # Check embedding model
        embedding_status = "healthy" if document_processor.embedding_model else "unhealthy"
        
        # Check database connection
        db_manager = get_database_manager()
        db_status = "healthy" if db_manager else "unhealthy"
        
        health_status = {
            "service": "document_processor",
            "status": "healthy",
            "chromadb": chromadb_status,
            "embedding_model": embedding_status,
            "database": db_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Document processor health check failed: {str(e)}")
        return {
            "service": "document_processor",
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# Add datetime import for timestamps
from datetime import datetime
