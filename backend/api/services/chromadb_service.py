"""
ChromaDB Service for Vector Storage and Document Management
Handles document collections, embeddings, and vector search operations
"""
import logging
import uuid
import os
from typing import List, Dict, Any, Optional, Tuple
import chromadb
from chromadb.config import Settings
from chromadb.api.models.Collection import Collection
import json
from datetime import datetime

# Disable ChromaDB telemetry
os.environ["ANONYMIZED_TELEMETRY"] = "False"

# Suppress ChromaDB telemetry error messages
logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.CRITICAL)

logger = logging.getLogger(__name__)

class ChromaDBService:
    def __init__(self, chroma_url: str = "http://localhost:8001"):
        """
        Initialize ChromaDB service
        
        Args:
            chroma_url: ChromaDB server URL
        """
        self.chroma_url = chroma_url
        self.client = None
        self.collections = {}
        self.logger = logger
        
    def initialize(self):
        """Initialize ChromaDB client and create collections"""
        try:
            # Initialize ChromaDB client - try PersistentClient first, fallback to HttpClient
            try:
                # Try PersistentClient for local development with telemetry disabled
                settings = Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
                self.client = chromadb.PersistentClient(
                    path="./chroma_db",
                    settings=settings
                )
            except Exception as e:
                self.logger.warning(f"PersistentClient failed, trying HttpClient: {str(e)}")
                # Fallback to HttpClient with telemetry disabled
                settings = Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
                self.client = chromadb.HttpClient(
                    host="localhost",
                    port=8001,
                    settings=settings
                )
            
            # Create document collections
            self._create_collections()
            
            self.logger.info("ChromaDB service initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize ChromaDB service: {str(e)}")
            raise
    
    def _create_collections(self):
        """Create all required document collections"""
        collections_config = {
            "employee_documents": {
                "description": "Employee-related documents (resumes, contracts, reviews)",
                "metadata": {"type": "employee", "category": "general"}
            },
            "resume_chunks": {
                "description": "Resume text chunks with embeddings",
                "metadata": {"type": "resume", "category": "chunk"}
            },
            "contract_chunks": {
                "description": "Contract text chunks with embeddings",
                "metadata": {"type": "contract", "category": "chunk"}
            },
            "review_chunks": {
                "description": "Performance review text chunks with embeddings",
                "metadata": {"type": "review", "category": "chunk"}
            },
            "policy_chunks": {
                "description": "Company policy text chunks with embeddings",
                "metadata": {"type": "policy", "category": "chunk"}
            }
        }
        
        for collection_name, config in collections_config.items():
            try:
                # Get or create collection
                collection = self.client.get_or_create_collection(
                    name=collection_name,
                    metadata=config["metadata"]
                )
                self.collections[collection_name] = collection
                self.logger.info(f"Collection '{collection_name}' ready")
                
            except Exception as e:
                self.logger.error(f"Failed to create collection '{collection_name}': {str(e)}")
                raise
    
    def add_document_chunks(
        self, 
        collection_name: str, 
        chunks: List[Dict[str, Any]], 
        document_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Add document chunks to a collection
        
        Args:
            collection_name: Name of the collection
            chunks: List of text chunks with metadata
            document_id: Unique document identifier
            metadata: Additional metadata for the document
            
        Returns:
            List of chunk IDs
        """
        try:
            if collection_name not in self.collections:
                raise ValueError(f"Collection '{collection_name}' not found")
            
            collection = self.collections[collection_name]
            chunk_ids = []
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{document_id}_chunk_{i}"
                chunk_metadata = {
                    "document_id": document_id,
                    "chunk_index": i,
                    "created_at": datetime.utcnow().isoformat(),
                    **(metadata or {}),
                    **(chunk.get("metadata", {}))
                }
                
                # Add chunk to collection
                collection.add(
                    documents=[chunk["text"]],
                    ids=[chunk_id],
                    metadatas=[chunk_metadata]
                )
                
                chunk_ids.append(chunk_id)
            
            self.logger.info(f"Added {len(chunks)} chunks to collection '{collection_name}'")
            return chunk_ids
            
        except Exception as e:
            self.logger.error(f"Failed to add document chunks: {str(e)}")
            raise
    
    def search_similar_chunks(
        self, 
        collection_name: str, 
        query_text: str, 
        n_results: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks using vector similarity
        
        Args:
            collection_name: Name of the collection to search
            query_text: Query text for similarity search
            n_results: Number of results to return
            filter_metadata: Metadata filters for the search
            
        Returns:
            List of similar chunks with metadata
        """
        try:
            if collection_name not in self.collections:
                raise ValueError(f"Collection '{collection_name}' not found")
            
            collection = self.collections[collection_name]
            
            # Perform similarity search
            results = collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=filter_metadata
            )
            
            # Format results
            similar_chunks = []
            if results["documents"] and results["documents"][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0]
                )):
                    similar_chunks.append({
                        "chunk_id": results["ids"][0][i],
                        "text": doc,
                        "metadata": metadata,
                        "similarity_score": 1 - distance,  # Convert distance to similarity
                        "distance": distance
                    })
            
            self.logger.info(f"Found {len(similar_chunks)} similar chunks in '{collection_name}'")
            return similar_chunks
            
        except Exception as e:
            self.logger.error(f"Failed to search similar chunks: {str(e)}")
            raise
    
    def get_document_chunks(
        self, 
        collection_name: str, 
        document_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all chunks for a specific document
        
        Args:
            collection_name: Name of the collection
            document_id: Document identifier
            
        Returns:
            List of document chunks
        """
        try:
            if collection_name not in self.collections:
                raise ValueError(f"Collection '{collection_name}' not found")
            
            collection = self.collections[collection_name]
            
            # Get chunks by document ID
            results = collection.get(
                where={"document_id": document_id}
            )
            
            chunks = []
            if results["documents"]:
                for i, (doc, metadata) in enumerate(zip(
                    results["documents"],
                    results["metadatas"]
                )):
                    chunks.append({
                        "chunk_id": results["ids"][i],
                        "text": doc,
                        "metadata": metadata
                    })
            
            return chunks
            
        except Exception as e:
            self.logger.error(f"Failed to get document chunks: {str(e)}")
            raise
    
    def delete_document_chunks(
        self, 
        collection_name: str, 
        document_id: str
    ) -> bool:
        """
        Delete all chunks for a specific document
        
        Args:
            collection_name: Name of the collection
            document_id: Document identifier
            
        Returns:
            True if successful
        """
        try:
            if collection_name not in self.collections:
                raise ValueError(f"Collection '{collection_name}' not found")
            
            collection = self.collections[collection_name]
            
            # Get chunk IDs for the document
            results = collection.get(
                where={"document_id": document_id}
            )
            
            if results["ids"]:
                # Delete chunks
                collection.delete(ids=results["ids"])
                self.logger.info(f"Deleted {len(results['ids'])} chunks for document '{document_id}'")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete document chunks: {str(e)}")
            return False
    
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """
        Get information about a collection
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Collection information
        """
        try:
            if collection_name not in self.collections:
                raise ValueError(f"Collection '{collection_name}' not found")
            
            collection = self.collections[collection_name]
            count = collection.count()
            
            return {
                "name": collection_name,
                "count": count,
                "metadata": collection.metadata
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get collection info: {str(e)}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform ChromaDB health check
        
        Returns:
            Health check results
        """
        try:
            # Test basic connectivity
            collections = self.client.list_collections()
            
            return {
                "status": "healthy",
                "collections": len(collections),
                "collection_names": [col.name for col in collections],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"ChromaDB health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_all_collections(self) -> Dict[str, Any]:
        """
        Get information about all collections
        
        Returns:
            Dictionary of collection information
        """
        try:
            collections_info = {}
            for name, collection in self.collections.items():
                collections_info[name] = self.get_collection_info(name)
            
            return collections_info
            
        except Exception as e:
            self.logger.error(f"Failed to get all collections: {str(e)}")
            raise

# Global ChromaDB service instance
chromadb_service: Optional[ChromaDBService] = None

def get_chromadb_service() -> ChromaDBService:
    """Get the global ChromaDB service instance"""
    if chromadb_service is None:
        raise RuntimeError("ChromaDB service not initialized")
    return chromadb_service

def initialize_chromadb_service(chroma_url: str) -> ChromaDBService:
    """Initialize the global ChromaDB service"""
    global chromadb_service
    chromadb_service = ChromaDBService(chroma_url)
    chromadb_service.initialize()
    return chromadb_service
