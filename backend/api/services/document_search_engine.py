"""
Document Search Engine
Vector-based document search using ChromaDB and embeddings
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json

from .chromadb_service import get_chromadb_service
from .document_processor import get_document_processor
from .redis_service import get_redis_service

logger = logging.getLogger(__name__)

class DocumentSearchEngine:
    """Vector-based document search using ChromaDB"""
    
    def __init__(self):
        self.logger = logger
        self.chromadb_service = None
        self.document_processor = None
        self.redis_service = None
        
        # Search configuration
        self.search_config = {
            "default_limit": 10,
            "max_limit": 100,
            "similarity_threshold": 0.3,  # Lowered threshold for better results
            "cache_ttl": 3600  # 1 hour
        }
        
        # Collection priorities for search
        self.collection_priorities = {
            "resume_chunks": 1.0,
            "contract_chunks": 0.9,
            "review_chunks": 0.8,
            "policy_chunks": 0.7,
            "employee_documents": 0.6
        }
    
    def initialize(self):
        """Initialize the document search engine"""
        try:
            # Initialize services
            self.chromadb_service = get_chromadb_service()
            self.document_processor = get_document_processor()
            self.redis_service = get_redis_service()
            
            self.logger.info("Document search engine initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize document search engine: {str(e)}")
            raise
    
    def search_documents(self, query: str, doc_type: Optional[str] = None, limit: int = 10, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Search documents using vector similarity
        
        Args:
            query: Search query
            doc_type: Optional document type filter
            limit: Maximum number of results
            filters: Optional search filters
            
        Returns:
            Search results with documents, scores, and metadata
        """
        try:
            self.logger.info(f"Searching documents for query: {query[:100]}...")
            
            # Validate parameters
            limit = min(limit, self.search_config["max_limit"])
            
            # Check cache first
            cache_key = f"document_search:{hash(query)}:{doc_type}:{limit}"
            cached_result = self._get_cached_search(cache_key)
            if cached_result:
                self.logger.info("Using cached search results")
                return cached_result
            
            # Generate query embedding
            query_embedding = self._generate_query_embedding(query)
            if not query_embedding:
                return {
                    "success": False,
                    "error": "Failed to generate query embedding",
                    "results": [],
                    "total_results": 0
                }
            
            # Determine collections to search
            collections_to_search = self._get_collections_to_search(doc_type)
            
            # Search in collections
            all_results = []
            for collection_name in collections_to_search:
                try:
                    collection_results = self._search_collection(
                        collection_name, query_embedding, limit, filters
                    )
                    all_results.extend(collection_results)
                except Exception as e:
                    self.logger.warning(f"Failed to search collection {collection_name}: {str(e)}")
                    continue
            
            # Rank and score results
            ranked_results = self._rank_search_results(all_results, query)
            
            # Apply final limit
            final_results = ranked_results[:limit]
            
            # Prepare response
            search_result = {
                "success": True,
                "query": query,
                "results": final_results,
                "total_results": len(final_results),
                "collections_searched": collections_to_search,
                "search_time": datetime.utcnow().isoformat()
            }
            
            # Cache result
            self._cache_search(cache_key, search_result)
            
            self.logger.info(f"Document search completed: {len(final_results)} results found")
            
            return search_result
            
        except Exception as e:
            self.logger.error(f"Document search failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "results": [],
                "total_results": 0
            }
    
    def _generate_query_embedding(self, query: str) -> Optional[List[float]]:
        """Generate embedding for search query"""
        try:
            if not self.document_processor or not self.document_processor.embedding_model:
                raise ValueError("Document processor or embedding model not available")
            
            # Generate embedding
            embedding = self.document_processor.embedding_model.encode([query])[0].tolist()
            
            return embedding
            
        except Exception as e:
            self.logger.error(f"Failed to generate query embedding: {str(e)}")
            return None
    
    def _get_collections_to_search(self, doc_type: Optional[str] = None) -> List[str]:
        """Get collections to search based on document type"""
        try:
            if not self.chromadb_service or not self.chromadb_service.client:
                return []
            
            # Default collections
            all_collections = [
                "employee_documents",
                "resume_chunks",
                "contract_chunks",
                "review_chunks",
                "policy_chunks"
            ]
            
            if doc_type:
                # Filter by document type
                type_mapping = {
                    "resume": ["resume_chunks"],
                    "contract": ["contract_chunks"],
                    "review": ["review_chunks"],
                    "policy": ["policy_chunks"],
                    "document": ["employee_documents"]
                }
                
                collections = type_mapping.get(doc_type.lower(), all_collections)
            else:
                collections = all_collections
            
            # Check which collections exist
            available_collections = []
            for collection_name in collections:
                try:
                    self.chromadb_service.client.get_collection(collection_name)
                    available_collections.append(collection_name)
                except Exception:
                    # Collection doesn't exist, skip it
                    continue
            
            return available_collections
            
        except Exception as e:
            self.logger.error(f"Failed to get collections to search: {str(e)}")
            return []
    
    def _search_collection(self, collection_name: str, query_embedding: List[float], limit: int, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search a specific collection"""
        try:
            if not self.chromadb_service or not self.chromadb_service.client:
                return []
            
            # Get collection
            collection = self.chromadb_service.client.get_collection(collection_name)
            
            # Prepare where clause for filters
            where_clause = None
            if filters:
                where_clause = self._build_where_clause(filters)
            
            # Search in collection
            search_results = collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_clause
            )
            
            # Process results
            results = []
            if search_results["documents"] and search_results["documents"][0]:
                for i, doc in enumerate(search_results["documents"][0]):
                    result = {
                        "document": doc,
                        "metadata": search_results["metadatas"][0][i] if search_results["metadatas"] else {},
                        "distance": search_results["distances"][0][i] if search_results["distances"] else 0.0,
                        "collection": collection_name,
                        "similarity_score": 1.0 - (search_results["distances"][0][i] if search_results["distances"] else 0.0)
                    }
                    results.append(result)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to search collection {collection_name}: {str(e)}")
            return []
    
    def _build_where_clause(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Build where clause for ChromaDB filters"""
        try:
            where_clause = {}
            
            for key, value in filters.items():
                if isinstance(value, str):
                    where_clause[key] = {"$eq": value}
                elif isinstance(value, list):
                    where_clause[key] = {"$in": value}
                elif isinstance(value, dict):
                    where_clause[key] = value
            
            return where_clause
            
        except Exception as e:
            self.logger.error(f"Failed to build where clause: {str(e)}")
            return {}
    
    def _rank_search_results(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Rank search results by relevance and quality"""
        try:
            if not results:
                return []
            
            # Calculate ranking scores
            for result in results:
                # Base similarity score
                similarity_score = result.get("similarity_score", 0.0)
                
                # Collection priority score
                collection = result.get("collection", "")
                priority_score = self.collection_priorities.get(collection, 0.5)
                
                # Content quality score
                content_score = self._calculate_content_quality(result, query)
                
                # Metadata bonus
                metadata_score = self._calculate_metadata_bonus(result)
                
                # Combined ranking score
                ranking_score = (
                    similarity_score * 0.4 +
                    priority_score * 0.2 +
                    content_score * 0.2 +
                    metadata_score * 0.2
                )
                
                result["ranking_score"] = ranking_score
                result["content_quality"] = content_score
                result["metadata_bonus"] = metadata_score
            
            # Sort by ranking score
            ranked_results = sorted(results, key=lambda x: x.get("ranking_score", 0.0), reverse=True)
            
            # Filter by similarity threshold
            filtered_results = [
                result for result in ranked_results
                if result.get("similarity_score", 0.0) >= self.search_config["similarity_threshold"]
            ]
            
            return filtered_results
            
        except Exception as e:
            self.logger.error(f"Failed to rank search results: {str(e)}")
            return results
    
    def _calculate_content_quality(self, result: Dict[str, Any], query: str) -> float:
        """Calculate content quality score"""
        try:
            document = result.get("document", "")
            if not document:
                return 0.0
            
            # Length score (prefer longer, more detailed content)
            length_score = min(1.0, len(document) / 1000)  # Normalize to 1000 chars
            
            # Keyword density score
            query_words = query.lower().split()
            document_lower = document.lower()
            keyword_matches = sum(1 for word in query_words if word in document_lower)
            keyword_score = min(1.0, keyword_matches / len(query_words)) if query_words else 0.0
            
            # Structure score (prefer well-structured content)
            structure_score = 0.5  # Base score
            if any(marker in document for marker in [".", "!", "?"]):  # Has sentences
                structure_score += 0.2
            if any(marker in document for marker in ["\n", "\t"]):  # Has structure
                structure_score += 0.2
            if len(document.split()) > 10:  # Has substantial content
                structure_score += 0.1
            
            # Combined quality score
            quality_score = (length_score * 0.3 + keyword_score * 0.4 + structure_score * 0.3)
            
            return min(1.0, quality_score)
            
        except Exception as e:
            self.logger.error(f"Failed to calculate content quality: {str(e)}")
            return 0.5
    
    def _calculate_metadata_bonus(self, result: Dict[str, Any]) -> float:
        """Calculate metadata bonus score"""
        try:
            metadata = result.get("metadata", {})
            bonus_score = 0.0
            
            # Document type bonus
            doc_type = metadata.get("doc_type", "")
            if doc_type:
                bonus_score += 0.1
            
            # Section type bonus
            section_type = metadata.get("section_type", "")
            if section_type and section_type != "unknown":
                bonus_score += 0.1
            
            # Chunk type bonus
            chunk_type = metadata.get("chunk_type", "")
            if chunk_type and chunk_type != "unknown":
                bonus_score += 0.1
            
            # Recent document bonus
            created_at = metadata.get("created_at", "")
            if created_at:
                try:
                    from datetime import datetime
                    doc_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    days_old = (datetime.utcnow() - doc_date).days
                    if days_old < 30:  # Recent document
                        bonus_score += 0.1
                except Exception:
                    pass
            
            return min(1.0, bonus_score)
            
        except Exception as e:
            self.logger.error(f"Failed to calculate metadata bonus: {str(e)}")
            return 0.0
    
    def get_document_by_id(self, document_id: str, chunk_id: Optional[str] = None) -> Dict[str, Any]:
        """Get specific document by ID"""
        try:
            if not self.chromadb_service or not self.chromadb_service.client:
                return {"success": False, "error": "ChromaDB service not available"}
            
            # Search across all collections
            collections = [
                "employee_documents",
                "resume_chunks",
                "contract_chunks",
                "review_chunks",
                "policy_chunks"
            ]
            
            for collection_name in collections:
                try:
                    collection = self.chromadb_service.client.get_collection(collection_name)
                    
                    # Search by document ID
                    results = collection.get(
                        where={"document_id": document_id},
                        include=["documents", "metadatas"]
                    )
                    
                    if results["documents"]:
                        # Return first match
                        return {
                            "success": True,
                            "document": results["documents"][0],
                            "metadata": results["metadatas"][0] if results["metadatas"] else {},
                            "collection": collection_name
                        }
                        
                except Exception as e:
                    self.logger.warning(f"Failed to search collection {collection_name}: {str(e)}")
                    continue
            
            return {"success": False, "error": "Document not found"}
            
        except Exception as e:
            self.logger.error(f"Failed to get document by ID: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics for all collections"""
        try:
            if not self.chromadb_service or not self.chromadb_service.client:
                return {"error": "ChromaDB service not available"}
            
            collections = [
                "employee_documents",
                "resume_chunks",
                "contract_chunks",
                "review_chunks",
                "policy_chunks"
            ]
            
            stats = {}
            total_documents = 0
            
            for collection_name in collections:
                try:
                    collection = self.chromadb_service.client.get_collection(collection_name)
                    count = collection.count()
                    stats[collection_name] = {
                        "count": count,
                        "type": "document" if collection_name == "employee_documents" else "chunk"
                    }
                    total_documents += count
                except Exception as e:
                    stats[collection_name] = {
                        "count": 0,
                        "type": "document" if collection_name == "employee_documents" else "chunk",
                        "error": str(e)
                    }
            
            stats["total_documents"] = total_documents
            stats["collections_count"] = len(collections)
            
            return {"success": True, "stats": stats}
            
        except Exception as e:
            self.logger.error(f"Failed to get collection stats: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _get_cached_search(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached search result"""
        try:
            if not self.redis_service:
                return None
            
            cached_result = self.redis_service.get(cache_key)
            if cached_result:
                # Handle both string and dict results
                if isinstance(cached_result, str):
                    return json.loads(cached_result)
                elif isinstance(cached_result, dict):
                    return cached_result
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get cached search: {str(e)}")
            return None
    
    def _cache_search(self, cache_key: str, result: Dict[str, Any]):
        """Cache search result"""
        try:
            if not self.redis_service:
                return
            
            # Cache for configured TTL
            self.redis_service.set(cache_key, json.dumps(result), ttl=self.search_config["cache_ttl"])
            
        except Exception as e:
            self.logger.error(f"Failed to cache search: {str(e)}")

# Global document search engine instance
document_search_engine: Optional[DocumentSearchEngine] = None

def get_document_search_engine() -> DocumentSearchEngine:
    """Get the global document search engine instance"""
    if document_search_engine is None:
        raise RuntimeError("Document search engine not initialized")
    return document_search_engine

def initialize_document_search_engine() -> DocumentSearchEngine:
    """Initialize the global document search engine"""
    global document_search_engine
    document_search_engine = DocumentSearchEngine()
    document_search_engine.initialize()
    return document_search_engine
