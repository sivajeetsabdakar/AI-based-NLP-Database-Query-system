"""
Query Classification System
Intelligent query classification using Mistral API for query type detection
"""
import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json

from .mistral_client import get_mistral_client
from .database_utils import get_database_utils
from .redis_service import get_redis_service

logger = logging.getLogger(__name__)

class QueryClassifier:
    """Intelligent query classification using Mistral API"""
    
    def __init__(self):
        self.logger = logger
        self.mistral_client = None
        self.db_utils = None
        self.redis_service = None
        
        # Query classification patterns
        self.sql_indicators = [
            "how many", "count", "total", "sum", "average", "max", "min",
            "list", "show", "display", "get", "find", "search",
            "employees", "salary", "department", "position", "hire date",
            "database", "table", "record", "data"
        ]
        
        self.document_indicators = [
            "resume", "cv", "document", "file", "pdf", "contract",
            "review", "performance", "evaluation", "feedback",
            "policy", "procedure", "guideline", "manual",
            "skills", "experience", "education", "qualification"
        ]
        
        self.hybrid_indicators = [
            "with", "having", "containing", "including", "that have",
            "who", "which", "where", "when", "and", "or"
        ]
        
        # Query complexity patterns
        self.complexity_indicators = {
            "simple": ["count", "list", "show", "get"],
            "medium": ["average", "sum", "group by", "order by"],
            "complex": ["join", "subquery", "union", "having", "case when"]
        }
    
    def initialize(self):
        """Initialize the query classifier"""
        try:
            # Initialize services
            self.mistral_client = get_mistral_client()
            self.db_utils = get_database_utils()
            self.redis_service = get_redis_service()
            
            self.logger.info("Query classifier initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize query classifier: {str(e)}")
            raise
    
    def classify_query(self, query: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Classify a natural language query using Mistral API
        
        Args:
            query: Natural language query to classify
            user_context: Optional user context information
            
        Returns:
            Classification result with type, confidence, and metadata
        """
        try:
            self.logger.info(f"Classifying query: {query[:100]}...")
            
            # Check cache first
            cache_key = f"query_classification:{hash(query)}"
            cached_result = self._get_cached_classification(cache_key)
            if cached_result:
                self.logger.info("Using cached classification result")
                return cached_result
            
            # Preprocess query
            processed_query = self._preprocess_query(query)
            
            # Analyze query using Mistral API
            classification_result = self._analyze_query_with_mistral(processed_query, user_context)
            
            # Validate and enhance classification
            enhanced_result = self._enhance_classification(processed_query, classification_result)
            
            # Cache result
            self._cache_classification(cache_key, enhanced_result)
            
            self.logger.info(f"Query classified as: {enhanced_result['query_type']} (confidence: {enhanced_result['confidence']})")
            
            return enhanced_result
            
        except Exception as e:
            self.logger.error(f"Query classification failed: {str(e)}")
            return {
                "query": query,
                "query_type": "unknown",
                "confidence": 0.0,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _preprocess_query(self, query: str) -> str:
        """Preprocess query for better classification with security sanitization"""
        try:
            # Security: Remove potentially dangerous content FIRST
            query = self._sanitize_input(query)
            
            # Normalize whitespace
            processed = re.sub(r'\s+', ' ', query.strip())
            
            # Convert to lowercase for pattern matching
            processed_lower = processed.lower()
            
            # Remove common stop words that don't affect classification
            stop_words = ['please', 'can you', 'could you', 'i want', 'i need']
            for stop_word in stop_words:
                processed_lower = processed_lower.replace(stop_word, '')
            
            # Clean up extra spaces
            processed = re.sub(r'\s+', ' ', processed_lower.strip())
            
            return processed
            
        except Exception as e:
            self.logger.error(f"Query preprocessing failed: {str(e)}")
            return query
    
    def _sanitize_input(self, text: str) -> str:
        """Remove potentially dangerous content from input (XSS, command injection)"""
        try:
            # Remove script tags and their content
            text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
            
            # Remove other potentially dangerous HTML tags
            text = re.sub(r'<\s*(iframe|object|embed|applet|meta|link|style)[^>]*>.*?</\s*\1\s*>', '', text, flags=re.IGNORECASE | re.DOTALL)
            
            # Remove standalone HTML tags
            text = re.sub(r'<[^>]+>', '', text)
            
            # Remove javascript: protocol (XSS vector)
            text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
            
            # Remove data: protocol (XSS vector)
            text = re.sub(r'data:', '', text, flags=re.IGNORECASE)
            
            # Remove vbscript: protocol (XSS vector)
            text = re.sub(r'vbscript:', '', text, flags=re.IGNORECASE)
            
            # Remove command injection patterns
            dangerous_patterns = {
                '&&': ' and ',
                '||': ' or ',
                ';': ' ',
                '|': ' ',
                '`': "'",
                '$': '',
                '$(': '',
                '${': ''
            }
            
            for pattern, replacement in dangerous_patterns.items():
                text = text.replace(pattern, replacement)
            
            # Remove null bytes
            text = text.replace('\x00', '')
            
            return text.strip()
            
        except Exception as e:
            self.logger.error(f"Input sanitization failed: {str(e)}")
            return text
    
    def _analyze_query_with_mistral(self, query: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze query using Mistral API for intelligent classification"""
        try:
            if not self.mistral_client:
                raise ValueError("Mistral client not initialized")
            
            # Create classification prompt
            prompt = self._create_classification_prompt(query, user_context)
            
            # Get Mistral API response
            response = self.mistral_client.generate_response(prompt)
            
            # Parse response
            classification_result = self._parse_mistral_response(response)
            
            return classification_result
            
        except Exception as e:
            self.logger.error(f"Mistral API analysis failed: {str(e)}")
            # Fallback to pattern-based classification
            return self._fallback_classification(query)
    
    def _create_classification_prompt(self, query: str, user_context: Optional[Dict[str, Any]] = None) -> str:
        """Create prompt for Mistral API query classification"""
        prompt = f"""
You are an expert query classifier for an employee database system. Analyze the following natural language query and classify it into one of these categories:

1. SQL_QUERY: Queries that require database operations (counting, filtering, aggregating data)
2. DOCUMENT_QUERY: Queries that search through documents (resumes, contracts, reviews, policies)
3. HYBRID_QUERY: Queries that combine both database and document search

Query: "{query}"

Please respond with a JSON object containing:
- query_type: One of "SQL_QUERY", "DOCUMENT_QUERY", or "HYBRID_QUERY"
- confidence: Float between 0.0 and 1.0 indicating classification confidence
- reasoning: Brief explanation of why this classification was chosen
- entities: List of key entities mentioned in the query
- intent: The user's intent behind the query
- complexity: "simple", "medium", or "complex" based on query complexity

Examples:
- "How many employees do we have?" → SQL_QUERY
- "Show me resumes with Python skills" → DOCUMENT_QUERY  
- "Python developers earning over 100k" → HYBRID_QUERY

Respond only with valid JSON.
"""
        
        if user_context:
            prompt += f"\nUser Context: {json.dumps(user_context)}"
        
        return prompt
    
    def _parse_mistral_response(self, response: str) -> Dict[str, Any]:
        """Parse Mistral API response for classification"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                result = json.loads(json_str)
                
                # Validate required fields
                required_fields = ['query_type', 'confidence', 'reasoning', 'entities', 'intent', 'complexity']
                for field in required_fields:
                    if field not in result:
                        result[field] = self._get_default_value(field)
                
                return result
            else:
                # Fallback parsing
                return self._parse_text_response(response)
                
        except Exception as e:
            self.logger.error(f"Failed to parse Mistral response: {str(e)}")
            return self._get_default_classification()
    
    def _parse_text_response(self, response: str) -> Dict[str, Any]:
        """Parse text response when JSON parsing fails"""
        try:
            # Extract query type
            query_type = "unknown"
            if "SQL_QUERY" in response.upper():
                query_type = "SQL_QUERY"
            elif "DOCUMENT_QUERY" in response.upper():
                query_type = "DOCUMENT_QUERY"
            elif "HYBRID_QUERY" in response.upper():
                query_type = "HYBRID_QUERY"
            
            # Extract confidence (look for numbers)
            confidence = 0.5
            confidence_match = re.search(r'confidence[:\s]*([0-9.]+)', response, re.IGNORECASE)
            if confidence_match:
                confidence = float(confidence_match.group(1))
            
            # Extract entities
            entities = []
            if "entities" in response.lower():
                entity_match = re.search(r'entities[:\s]*\[(.*?)\]', response, re.IGNORECASE)
                if entity_match:
                    entities = [e.strip().strip('"') for e in entity_match.group(1).split(',')]
            
            return {
                "query_type": query_type,
                "confidence": confidence,
                "reasoning": response[:200] + "..." if len(response) > 200 else response,
                "entities": entities,
                "intent": "unknown",
                "complexity": "medium"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to parse text response: {str(e)}")
            return self._get_default_classification()
    
    def _get_default_classification(self) -> Dict[str, Any]:
        """Get default classification when parsing fails"""
        return {
            "query_type": "unknown",
            "confidence": 0.0,
            "reasoning": "Failed to parse response",
            "entities": [],
            "intent": "unknown",
            "complexity": "medium"
        }
    
    def _get_default_value(self, field: str) -> Any:
        """Get default value for missing field"""
        defaults = {
            "query_type": "unknown",
            "confidence": 0.5,
            "reasoning": "No reasoning provided",
            "entities": [],
            "intent": "unknown",
            "complexity": "medium"
        }
        return defaults.get(field, None)
    
    def _fallback_classification(self, query: str) -> Dict[str, Any]:
        """Fallback pattern-based classification when Mistral API fails"""
        try:
            query_lower = query.lower()
            
            # Count indicators for each type
            sql_score = sum(1 for indicator in self.sql_indicators if indicator in query_lower)
            document_score = sum(1 for indicator in self.document_indicators if indicator in query_lower)
            hybrid_score = sum(1 for indicator in self.hybrid_indicators if indicator in query_lower)
            
            # Determine query type
            if hybrid_score > 0 and (sql_score > 0 or document_score > 0):
                query_type = "HYBRID_QUERY"
                confidence = min(0.8, 0.5 + (hybrid_score * 0.1))
            elif sql_score > document_score:
                query_type = "SQL_QUERY"
                confidence = min(0.8, 0.5 + (sql_score * 0.1))
            elif document_score > 0:
                query_type = "DOCUMENT_QUERY"
                confidence = min(0.8, 0.5 + (document_score * 0.1))
            else:
                query_type = "SQL_QUERY"  # Default to SQL
                confidence = 0.3
            
            # Determine complexity
            complexity = "simple"
            for complex_indicator in self.complexity_indicators["complex"]:
                if complex_indicator in query_lower:
                    complexity = "complex"
                    break
            else:
                for medium_indicator in self.complexity_indicators["medium"]:
                    if medium_indicator in query_lower:
                        complexity = "medium"
                        break
            
            # Extract entities (simple pattern matching)
            entities = []
            for indicator in self.sql_indicators + self.document_indicators:
                if indicator in query_lower:
                    entities.append(indicator)
            
            return {
                "query_type": query_type,
                "confidence": confidence,
                "reasoning": f"Pattern-based classification: SQL={sql_score}, Document={document_score}, Hybrid={hybrid_score}",
                "entities": entities,
                "intent": "unknown",
                "complexity": complexity
            }
            
        except Exception as e:
            self.logger.error(f"Fallback classification failed: {str(e)}")
            return self._get_default_classification()
    
    def _enhance_classification(self, query: str, classification_result: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance classification with additional analysis"""
        try:
            # Add timestamp
            classification_result["timestamp"] = datetime.utcnow().isoformat()
            
            # Add query preprocessing info
            classification_result["original_query"] = query
            classification_result["processed_query"] = query
            
            # Validate confidence score
            confidence = classification_result.get("confidence", 0.0)
            if not isinstance(confidence, (int, float)) or confidence < 0.0 or confidence > 1.0:
                classification_result["confidence"] = 0.5
            
            # Validate query type
            valid_types = ["SQL_QUERY", "DOCUMENT_QUERY", "HYBRID_QUERY", "unknown"]
            if classification_result.get("query_type") not in valid_types:
                classification_result["query_type"] = "unknown"
            
            # Add complexity analysis
            complexity = self._analyze_complexity(query)
            classification_result["complexity"] = complexity
            
            # Add entity extraction
            entities = self._extract_entities(query)
            if entities:
                classification_result["entities"] = entities
            
            # Add intent analysis
            intent = self._analyze_intent(query, classification_result.get("query_type"))
            classification_result["intent"] = intent
            
            return classification_result
            
        except Exception as e:
            self.logger.error(f"Classification enhancement failed: {str(e)}")
            return classification_result
    
    def _analyze_complexity(self, query: str) -> str:
        """Analyze query complexity"""
        try:
            query_lower = query.lower()
            
            # Check for complex patterns
            complex_patterns = [
                r'\b(join|union|subquery|having|case when)\b',
                r'\b(and|or)\b.*\b(and|or)\b',  # Multiple conditions
                r'\b(group by|order by|having)\b',
                r'\b(avg|sum|count|max|min)\b.*\b(group by)\b'
            ]
            
            for pattern in complex_patterns:
                if re.search(pattern, query_lower):
                    return "complex"
            
            # Check for medium patterns
            medium_patterns = [
                r'\b(where|filter|search)\b',
                r'\b(avg|sum|count|max|min)\b',
                r'\b(and|or)\b'
            ]
            
            for pattern in medium_patterns:
                if re.search(pattern, query_lower):
                    return "medium"
            
            return "simple"
            
        except Exception as e:
            self.logger.error(f"Complexity analysis failed: {str(e)}")
            return "medium"
    
    def _extract_entities(self, query: str) -> List[str]:
        """Extract entities from query"""
        try:
            entities = []
            query_lower = query.lower()
            
            # Extract common entities
            entity_patterns = {
                "employee": ["employee", "staff", "worker", "person"],
                "department": ["department", "dept", "team", "division"],
                "salary": ["salary", "pay", "wage", "compensation", "income"],
                "position": ["position", "role", "job", "title"],
                "skill": ["skill", "ability", "competency", "expertise"],
                "experience": ["experience", "exp", "years", "background"],
                "education": ["education", "degree", "qualification", "diploma"]
            }
            
            for entity_type, patterns in entity_patterns.items():
                for pattern in patterns:
                    if pattern in query_lower:
                        entities.append(entity_type)
                        break
            
            return list(set(entities))  # Remove duplicates
            
        except Exception as e:
            self.logger.error(f"Entity extraction failed: {str(e)}")
            return []
    
    def _analyze_intent(self, query: str, query_type: str) -> str:
        """Analyze user intent"""
        try:
            query_lower = query.lower()
            
            # Intent patterns
            intent_patterns = {
                "count": ["how many", "count", "total", "number of"],
                "list": ["list", "show", "display", "get", "find"],
                "search": ["search", "find", "look for", "locate"],
                "analyze": ["analyze", "compare", "average", "sum", "max", "min"],
                "filter": ["filter", "where", "with", "having", "that have"]
            }
            
            for intent, patterns in intent_patterns.items():
                if any(pattern in query_lower for pattern in patterns):
                    return intent
            
            # Default intent based on query type
            if query_type == "SQL_QUERY":
                return "analyze"
            elif query_type == "DOCUMENT_QUERY":
                return "search"
            else:
                return "unknown"
                
        except Exception as e:
            self.logger.error(f"Intent analysis failed: {str(e)}")
            return "unknown"
    
    def _get_cached_classification(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached classification result"""
        try:
            if not self.redis_service:
                return None
            
            cached_result = self.redis_service.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get cached classification: {str(e)}")
            return None
    
    def _cache_classification(self, cache_key: str, result: Dict[str, Any]):
        """Cache classification result"""
        try:
            if not self.redis_service:
                return
            
            # Cache for 1 hour
            self.redis_service.set(cache_key, json.dumps(result), expire=3600)
            
        except Exception as e:
            self.logger.error(f"Failed to cache classification: {str(e)}")
    
    def get_classification_stats(self) -> Dict[str, Any]:
        """Get classification statistics"""
        try:
            if not self.redis_service:
                return {"error": "Redis service not available"}
            
            # Get cached classifications count
            pattern = "query_classification:*"
            keys = self.redis_service.scan_keys(pattern)
            
            stats = {
                "total_classifications": len(keys),
                "cache_hit_rate": 0.0,  # Would need to track hits/misses
                "average_confidence": 0.0,  # Would need to track confidences
                "query_types": {
                    "SQL_QUERY": 0,
                    "DOCUMENT_QUERY": 0,
                    "HYBRID_QUERY": 0,
                    "unknown": 0
                }
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get classification stats: {str(e)}")
            return {"error": str(e)}

# Global query classifier instance
query_classifier: Optional[QueryClassifier] = None

def get_query_classifier() -> QueryClassifier:
    """Get the global query classifier instance"""
    if query_classifier is None:
        raise RuntimeError("Query classifier not initialized")
    return query_classifier

def initialize_query_classifier() -> QueryClassifier:
    """Initialize the global query classifier"""
    global query_classifier
    query_classifier = QueryClassifier()
    query_classifier.initialize()
    return query_classifier
