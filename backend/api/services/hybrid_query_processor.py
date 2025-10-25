"""
Hybrid Query Processing
Combine SQL and document search results intelligently
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json

from .query_classifier import get_query_classifier
from .sql_generator import get_sql_generator
from .document_search_engine import get_document_search_engine
from .redis_service import get_redis_service

logger = logging.getLogger(__name__)

class HybridQueryProcessor:
    """Process hybrid queries combining SQL and document search"""
    
    def __init__(self):
        self.logger = logger
        self.query_classifier = None
        self.sql_generator = None
        self.document_search_engine = None
        self.redis_service = None
        
        # Hybrid processing configuration
        self.processing_config = {
            "max_sql_results": 1000,
            "max_document_results": 100,
            "result_merge_threshold": 0.7,
            "cache_ttl": 3600  # 1 hour
        }
        
        # Result ranking weights
        self.ranking_weights = {
            "sql_relevance": 0.4,
            "document_relevance": 0.3,
            "result_freshness": 0.1,
            "result_completeness": 0.2
        }
    
    def initialize(self):
        """Initialize the hybrid query processor"""
        try:
            # Initialize services
            self.query_classifier = get_query_classifier()
            self.sql_generator = get_sql_generator()
            self.document_search_engine = get_document_search_engine()
            self.redis_service = get_redis_service()
            
            self.logger.info("Hybrid query processor initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize hybrid query processor: {str(e)}")
            raise
    
    def process_hybrid_query(self, query: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process hybrid query combining SQL and document search
        
        Args:
            query: Natural language query
            user_context: Optional user context
            
        Returns:
            Hybrid processing result with combined results
        """
        try:
            self.logger.info(f"Processing hybrid query: {query[:100]}...")
            
            # Check cache first
            cache_key = f"hybrid_query:{hash(query)}"
            cached_result = self._get_cached_hybrid_result(cache_key)
            if cached_result:
                self.logger.info("Using cached hybrid query result")
                return cached_result
            
            # Classify query
            classification = self.query_classifier.classify_query(query, user_context)
            
            # Process based on classification
            if classification["query_type"] == "SQL_QUERY":
                result = self._process_sql_only(query, classification, user_context)
            elif classification["query_type"] == "DOCUMENT_QUERY":
                result = self._process_document_only(query, classification, user_context)
            elif classification["query_type"] == "HYBRID_QUERY":
                result = self._process_hybrid_combined(query, classification, user_context)
            else:
                result = self._process_unknown_query(query, classification, user_context)
            
            # Cache result
            self._cache_hybrid_result(cache_key, result)
            
            self.logger.info(f"Hybrid query processing completed: {result.get('total_results', 0)} results")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Hybrid query processing failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "results": [],
                "total_results": 0
            }
    
    def _process_sql_only(self, query: str, classification: Dict[str, Any], user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process SQL-only query"""
        try:
            # Generate SQL
            sql_result = self.sql_generator.generate_sql(query, user_context=user_context)
            
            if not sql_result.get("sql"):
                return {
                    "success": False,
                    "error": "Failed to generate SQL",
                    "query_type": "SQL_QUERY",
                    "results": [],
                    "total_results": 0
                }
            
            # Execute SQL
            execution_result = self.sql_generator.execute_sql(sql_result["sql"])
            
            if not execution_result["success"]:
                return {
                    "success": False,
                    "error": execution_result.get("error", "SQL execution failed"),
                    "query_type": "SQL_QUERY",
                    "results": [],
                    "total_results": 0
                }
            
            # Format results
            formatted_results = self._format_sql_results(execution_result["results"], query)
            
            return {
                "success": True,
                "query_type": "SQL_QUERY",
                "sql": sql_result["sql"],
                "results": formatted_results,
                "total_results": len(formatted_results),
                "execution_time": execution_result.get("timestamp"),
                "confidence": sql_result.get("confidence", 0.0)
            }
            
        except Exception as e:
            self.logger.error(f"SQL-only processing failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "query_type": "SQL_QUERY",
                "results": [],
                "total_results": 0
            }
    
    def _process_document_only(self, query: str, classification: Dict[str, Any], user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process document-only query"""
        try:
            # Extract document type from classification
            doc_type = None
            entities = classification.get("entities", [])
            if "resume" in entities or "cv" in entities:
                doc_type = "resume"
            elif "contract" in entities:
                doc_type = "contract"
            elif "review" in entities:
                doc_type = "review"
            elif "policy" in entities:
                doc_type = "policy"
            
            # Search documents
            search_result = self.document_search_engine.search_documents(
                query=query,
                doc_type=doc_type,
                limit=self.processing_config["max_document_results"]
            )
            
            if not search_result["success"]:
                return {
                    "success": False,
                    "error": search_result.get("error", "Document search failed"),
                    "query_type": "DOCUMENT_QUERY",
                    "results": [],
                    "total_results": 0
                }
            
            # Format results
            formatted_results = self._format_document_results(search_result["results"], query)
            
            return {
                "success": True,
                "query_type": "DOCUMENT_QUERY",
                "results": formatted_results,
                "total_results": len(formatted_results),
                "collections_searched": search_result.get("collections_searched", []),
                "confidence": classification.get("confidence", 0.0)
            }
            
        except Exception as e:
            self.logger.error(f"Document-only processing failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "query_type": "DOCUMENT_QUERY",
                "results": [],
                "total_results": 0
            }
    
    def _process_hybrid_combined(self, query: str, classification: Dict[str, Any], user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process hybrid query combining SQL and document search"""
        try:
            # Process SQL component
            sql_result = self._process_sql_component(query, classification, user_context)
            
            # Process document component
            document_result = self._process_document_component(query, classification, user_context)
            
            # Merge results
            merged_results = self._merge_hybrid_results(sql_result, document_result, query)
            
            return {
                "success": True,
                "query_type": "HYBRID_QUERY",
                "sql_results": sql_result,
                "document_results": document_result,
                "results": merged_results["results"],
                "total_results": merged_results["total_results"],
                "merge_strategy": merged_results["strategy"],
                "confidence": (sql_result.get("confidence", 0.0) + document_result.get("confidence", 0.0)) / 2
            }
            
        except Exception as e:
            self.logger.error(f"Hybrid combined processing failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "query_type": "HYBRID_QUERY",
                "results": [],
                "total_results": 0
            }
    
    def _process_sql_component(self, query: str, classification: Dict[str, Any], user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process SQL component of hybrid query"""
        try:
            # Generate SQL
            sql_result = self.sql_generator.generate_sql(query, user_context=user_context)
            
            if not sql_result.get("sql"):
                return {"success": False, "error": "Failed to generate SQL", "results": []}
            
            # Execute SQL
            execution_result = self.sql_generator.execute_sql(sql_result["sql"])
            
            if not execution_result["success"]:
                return {"success": False, "error": execution_result.get("error"), "results": []}
            
            return {
                "success": True,
                "sql": sql_result["sql"],
                "results": execution_result["results"],
                "confidence": sql_result.get("confidence", 0.0)
            }
            
        except Exception as e:
            self.logger.error(f"SQL component processing failed: {str(e)}")
            return {"success": False, "error": str(e), "results": []}
    
    def _process_document_component(self, query: str, classification: Dict[str, Any], user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process document component of hybrid query"""
        try:
            # Extract document type
            doc_type = None
            entities = classification.get("entities", [])
            if "resume" in entities or "cv" in entities:
                doc_type = "resume"
            elif "contract" in entities:
                doc_type = "contract"
            elif "review" in entities:
                doc_type = "review"
            elif "policy" in entities:
                doc_type = "policy"
            
            # Search documents
            search_result = self.document_search_engine.search_documents(
                query=query,
                doc_type=doc_type,
                limit=self.processing_config["max_document_results"]
            )
            
            return {
                "success": search_result["success"],
                "results": search_result.get("results", []),
                "confidence": 0.8 if search_result["success"] else 0.0
            }
            
        except Exception as e:
            self.logger.error(f"Document component processing failed: {str(e)}")
            return {"success": False, "error": str(e), "results": []}
    
    def _merge_hybrid_results(self, sql_result: Dict[str, Any], document_result: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Merge SQL and document search results"""
        try:
            sql_results = sql_result.get("results", []) if sql_result.get("success") else []
            document_results = document_result.get("results", []) if document_result.get("success") else []
            
            # Determine merge strategy
            merge_strategy = self._determine_merge_strategy(sql_results, document_results, query)
            
            if merge_strategy == "sql_primary":
                # Use SQL results as primary, supplement with documents
                merged_results = self._merge_sql_primary(sql_results, document_results)
            elif merge_strategy == "document_primary":
                # Use document results as primary, supplement with SQL
                merged_results = self._merge_document_primary(sql_results, document_results)
            else:
                # Combine both result types
                merged_results = self._merge_combined(sql_results, document_results)
            
            return {
                "results": merged_results,
                "total_results": len(merged_results),
                "strategy": merge_strategy
            }
            
        except Exception as e:
            self.logger.error(f"Result merging failed: {str(e)}")
            return {
                "results": [],
                "total_results": 0,
                "strategy": "error"
            }
    
    def _determine_merge_strategy(self, sql_results: List[Any], document_results: List[Any], query: str) -> str:
        """Determine the best merge strategy"""
        try:
            query_lower = query.lower()
            
            # Check for specific patterns
            if any(pattern in query_lower for pattern in ["how many", "count", "total", "number of"]):
                return "sql_primary"
            elif any(pattern in query_lower for pattern in ["show me", "find", "search", "resume", "document"]):
                return "document_primary"
            elif len(sql_results) > len(document_results) * 2:
                return "sql_primary"
            elif len(document_results) > len(sql_results) * 2:
                return "document_primary"
            else:
                return "combined"
                
        except Exception as e:
            self.logger.error(f"Merge strategy determination failed: {str(e)}")
            return "combined"
    
    def _merge_sql_primary(self, sql_results: List[Any], document_results: List[Any]) -> List[Dict[str, Any]]:
        """Merge results with SQL as primary"""
        try:
            merged = []
            
            # Add SQL results
            for i, result in enumerate(sql_results):
                merged.append({
                    "type": "sql",
                    "data": result,
                    "rank": i + 1,
                    "source": "database"
                })
            
            # Add top document results
            for i, result in enumerate(document_results[:5]):  # Top 5 documents
                merged.append({
                    "type": "document",
                    "data": result,
                    "rank": len(sql_results) + i + 1,
                    "source": "documents"
                })
            
            return merged
            
        except Exception as e:
            self.logger.error(f"SQL primary merge failed: {str(e)}")
            return []
    
    def _merge_document_primary(self, sql_results: List[Any], document_results: List[Any]) -> List[Dict[str, Any]]:
        """Merge results with documents as primary"""
        try:
            merged = []
            
            # Add document results
            for i, result in enumerate(document_results):
                merged.append({
                    "type": "document",
                    "data": result,
                    "rank": i + 1,
                    "source": "documents"
                })
            
            # Add top SQL results
            for i, result in enumerate(sql_results[:5]):  # Top 5 SQL results
                merged.append({
                    "type": "sql",
                    "data": result,
                    "rank": len(document_results) + i + 1,
                    "source": "database"
                })
            
            return merged
            
        except Exception as e:
            self.logger.error(f"Document primary merge failed: {str(e)}")
            return []
    
    def _merge_combined(self, sql_results: List[Any], document_results: List[Any]) -> List[Dict[str, Any]]:
        """Combine both result types"""
        try:
            merged = []
            
            # Interleave results
            max_results = max(len(sql_results), len(document_results))
            
            for i in range(max_results):
                # Add SQL result if available
                if i < len(sql_results):
                    merged.append({
                        "type": "sql",
                        "data": sql_results[i],
                        "rank": len(merged) + 1,
                        "source": "database"
                    })
                
                # Add document result if available
                if i < len(document_results):
                    merged.append({
                        "type": "document",
                        "data": document_results[i],
                        "rank": len(merged) + 1,
                        "source": "documents"
                    })
            
            return merged
            
        except Exception as e:
            self.logger.error(f"Combined merge failed: {str(e)}")
            return []
    
    def _format_sql_results(self, sql_results: List[Any], query: str) -> List[Dict[str, Any]]:
        """Format SQL results for display"""
        try:
            formatted = []
            
            for i, result in enumerate(sql_results):
                formatted.append({
                    "id": f"sql_{i}",
                    "type": "sql",
                    "data": result,
                    "relevance_score": 1.0 - (i * 0.1),  # Decreasing relevance
                    "source": "database"
                })
            
            return formatted
            
        except Exception as e:
            self.logger.error(f"SQL result formatting failed: {str(e)}")
            return []
    
    def _format_document_results(self, document_results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Format document results for display"""
        try:
            formatted = []
            
            for result in document_results:
                formatted.append({
                    "id": f"doc_{result.get('metadata', {}).get('chunk_index', 0)}",
                    "type": "document",
                    "data": result,
                    "relevance_score": result.get("similarity_score", 0.0),
                    "source": "documents"
                })
            
            return formatted
            
        except Exception as e:
            self.logger.error(f"Document result formatting failed: {str(e)}")
            return []
    
    def _process_unknown_query(self, query: str, classification: Dict[str, Any], user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process unknown query type"""
        try:
            # Try both SQL and document search
            sql_result = self._process_sql_component(query, classification, user_context)
            document_result = self._process_document_component(query, classification, user_context)
            
            # Combine results
            merged_results = self._merge_combined(
                sql_result.get("results", []),
                document_result.get("results", [])
            )
            
            return {
                "success": True,
                "query_type": "UNKNOWN",
                "results": merged_results,
                "total_results": len(merged_results),
                "confidence": 0.3  # Low confidence for unknown type
            }
            
        except Exception as e:
            self.logger.error(f"Unknown query processing failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "query_type": "UNKNOWN",
                "results": [],
                "total_results": 0
            }
    
    def _get_cached_hybrid_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached hybrid query result"""
        try:
            if not self.redis_service:
                return None
            
            cached_result = self.redis_service.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get cached hybrid result: {str(e)}")
            return None
    
    def _cache_hybrid_result(self, cache_key: str, result: Dict[str, Any]):
        """Cache hybrid query result"""
        try:
            if not self.redis_service:
                return
            
            # Cache for configured TTL
            self.redis_service.set(cache_key, json.dumps(result), expire=self.processing_config["cache_ttl"])
            
        except Exception as e:
            self.logger.error(f"Failed to cache hybrid result: {str(e)}")

# Global hybrid query processor instance
hybrid_query_processor: Optional[HybridQueryProcessor] = None

def get_hybrid_query_processor() -> HybridQueryProcessor:
    """Get the global hybrid query processor instance"""
    if hybrid_query_processor is None:
        raise RuntimeError("Hybrid query processor not initialized")
    return hybrid_query_processor

def initialize_hybrid_query_processor() -> HybridQueryProcessor:
    """Initialize the global hybrid query processor"""
    global hybrid_query_processor
    hybrid_query_processor = HybridQueryProcessor()
    hybrid_query_processor.initialize()
    return hybrid_query_processor
