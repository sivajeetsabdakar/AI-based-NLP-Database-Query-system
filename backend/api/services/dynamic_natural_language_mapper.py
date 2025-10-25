"""
Truly Dynamic Natural Language to Schema Mapping System
Uses Mistral LLM for intelligent mapping without hard-coded patterns
"""
import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from .mistral_client import MistralClient

logger = logging.getLogger(__name__)

class DynamicNaturalLanguageMapper:
    """Truly dynamic natural language to schema mapping using Mistral LLM"""
    
    def __init__(self):
        self.logger = logger
        self.mistral_client = MistralClient()
    
    def map_query_to_schema(self, query: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map natural language query to database schema using Mistral LLM
        
        Args:
            query: Natural language query
            schema: Discovered database schema
            
        Returns:
            Mapping results with table and column suggestions
        """
        try:
            self.logger.info(f"Dynamic mapping query to schema: {query}")
            
            # Use Mistral LLM to extract entities and analyze query
            entities = self._extract_entities_with_llm(query)
            
            # Use Mistral LLM to find matching tables
            table_matches = self._find_matching_tables_with_llm(entities, schema)
            
            # Use Mistral LLM to find matching columns
            column_matches = self._find_matching_columns_with_llm(entities, schema, table_matches)
            
            # Use Mistral LLM to detect query intent
            intent = self._detect_query_intent_with_llm(query)
            
            # Use Mistral LLM to generate SQL suggestions
            sql_suggestions = self._generate_sql_suggestions_with_llm(query, table_matches, column_matches, intent)
            
            mapping_result = {
                "query": query,
                "entities": entities,
                "table_matches": table_matches,
                "column_matches": column_matches,
                "intent": intent,
                "query_type": intent.get("intent", "unknown"),  # Add for backward compatibility
                "sql_suggestions": sql_suggestions,
                "confidence": self._calculate_overall_confidence_with_llm(table_matches, column_matches),
                "mapping_timestamp": self._get_timestamp(),
                "analysis_method": "mistral_llm_dynamic"
            }
            
            self.logger.info(f"Dynamic query mapping completed with confidence: {mapping_result['confidence']}")
            return mapping_result
            
        except Exception as e:
            self.logger.error(f"Dynamic query mapping failed: {str(e)}")
            return {
                "query": query,
                "error": str(e),
                "confidence": 0.0,
                "analysis_method": "error"
            }
    
    def _extract_entities_with_llm(self, query: str) -> Dict[str, List[str]]:
        """Use Mistral LLM to extract entities from natural language query"""
        try:
            # Create prompt for entity extraction
            prompt = f"""
            Extract entities and analyze this natural language database query. Be intelligent and adaptive.
            
            Query: "{query}"
            
            Return JSON with:
            1. keywords: Important words and phrases
            2. entities: Specific entities mentioned (people, departments, amounts, dates, etc.)
            3. intent: What the user wants to do (list, count, filter, aggregate, etc.)
            4. filters: Any filtering conditions mentioned
            5. aggregations: Any aggregation operations (sum, average, count, etc.)
            6. sorting: Any sorting requirements
            7. business_context: What business domain this query relates to
            
            Be intelligent and look for patterns, not just keywords.
            """
            
            # Get LLM analysis
            llm_response = self.mistral_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model="mistral-small-latest"
            )
            
            if llm_response.get("success"):
                try:
                    content = llm_response.get("content", "{}")
                    json_start = content.find('{')
                    json_end = content.rfind('}') + 1
                    if json_start != -1 and json_end != -1:
                        json_content = content[json_start:json_end]
                        entities = json.loads(json_content)
                        return entities
                except Exception as e:
                    self.logger.warning(f"Failed to parse entity extraction LLM response: {str(e)}")
            
            # Fallback to simple extraction
            return self._fallback_entity_extraction(query)
            
        except Exception as e:
            self.logger.error(f"LLM entity extraction failed: {str(e)}")
            return self._fallback_entity_extraction(query)
    
    def _find_matching_tables_with_llm(self, entities: Dict[str, List[str]], schema: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Use Mistral LLM to find tables that match the query entities"""
        try:
            # Prepare table information for LLM analysis
            tables_info = {}
            for table_name, table_data in schema.get("tables", {}).items():
                tables_info[table_name] = {
                    "purpose": table_data.get("purpose", {}).get("primary_purpose", "unknown"),
                    "confidence": table_data.get("purpose", {}).get("confidence", 0.0),
                    "columns": list(table_data.get("columns", {}).keys()),
                    "row_count": table_data.get("row_count", 0)
                }
            
            # Create prompt for table matching
            prompt = f"""
            Analyze this natural language query and find the most relevant database tables. Be intelligent and adaptive.
            
            Query Entities: {json.dumps(entities, indent=2)}
            Available Tables: {json.dumps(tables_info, indent=2)}
            
            Return JSON with:
            1. relevant_tables: List of tables that match the query, ordered by relevance
            2. For each table:
               - table_name: Name of the table
               - relevance_score: How relevant (0.0 to 1.0)
               - reasoning: Why this table is relevant
               - confidence: How confident you are in this match
               - suggested_columns: Which columns might be useful
            
            Be intelligent and look for logical connections, not just keyword matches.
            """
            
            # Get LLM analysis
            llm_response = self.mistral_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model="mistral-small-latest"
            )
            
            if llm_response.get("success"):
                try:
                    content = llm_response.get("content", "{}")
                    json_start = content.find('{')
                    json_end = content.rfind('}') + 1
                    if json_start != -1 and json_end != -1:
                        json_content = content[json_start:json_end]
                        analysis = json.loads(json_content)
                        
                        matches = []
                        for table_info in analysis.get("relevant_tables", []):
                            matches.append({
                                "table_name": table_info.get("table_name"),
                                "purpose": tables_info.get(table_info.get("table_name", ""), {}).get("purpose", "unknown"),
                                "similarity_score": float(table_info.get("relevance_score", 0.0)),
                                "confidence": float(table_info.get("confidence", 0.0)),
                                "reasoning": table_info.get("reasoning", ""),
                                "suggested_columns": table_info.get("suggested_columns", []),
                                "row_count": tables_info.get(table_info.get("table_name", ""), {}).get("row_count", 0),
                                "analysis_method": "mistral_llm"
                            })
                        
                        return matches
                        
                except Exception as e:
                    self.logger.warning(f"Failed to parse table matching LLM response: {str(e)}")
            
            # Fallback to simple matching
            return self._fallback_table_matching(entities, schema)
            
        except Exception as e:
            self.logger.error(f"LLM table matching failed: {str(e)}")
            return self._fallback_table_matching(entities, schema)
    
    def _find_matching_columns_with_llm(self, entities: Dict[str, List[str]], schema: Dict[str, Any], table_matches: List[Dict]) -> Dict[str, List[Dict[str, Any]]]:
        """Use Mistral LLM to find columns that match the query entities"""
        try:
            column_matches = {}
            
            for table_match in table_matches[:3]:  # Limit to top 3 tables
                table_name = table_match["table_name"]
                table_info = schema.get("tables", {}).get(table_name, {})
                columns = table_info.get("columns", {})
                
                # Prepare column information for LLM
                columns_info = {}
                for col_name, col_info in columns.items():
                    columns_info[col_name] = {
                        "type": col_info.get("type", ""),
                        "purpose": col_info.get("purpose", {}).get("primary_purpose", "unknown"),
                        "sample_values": col_info.get("sample_values", [])[:3]
                    }
                
                # Create prompt for column matching
                prompt = f"""
                Analyze this query and find the most relevant columns in this table. Be intelligent and adaptive.
                
                Query Entities: {json.dumps(entities, indent=2)}
                Table: {table_name}
                Available Columns: {json.dumps(columns_info, indent=2)}
                
                Return JSON with:
                1. relevant_columns: List of columns that match the query, ordered by relevance
                2. For each column:
                   - column_name: Name of the column
                   - relevance_score: How relevant (0.0 to 1.0)
                   - reasoning: Why this column is relevant
                   - confidence: How confident you are in this match
                   - usage_suggestion: How this column might be used in the query
                
                Be intelligent and look for logical connections, not just keyword matches.
                """
                
                # Get LLM analysis
                llm_response = self.mistral_client.chat_completion(
                    messages=[{"role": "user", "content": prompt}],
                    model="mistral-small-latest"
                )
                
                if llm_response.get("success"):
                    try:
                        content = llm_response.get("content", "{}")
                        json_start = content.find('{')
                        json_end = content.rfind('}') + 1
                        if json_start != -1 and json_end != -1:
                            json_content = content[json_start:json_end]
                            analysis = json.loads(json_content)
                            
                            table_column_matches = []
                            for col_info in analysis.get("relevant_columns", []):
                                table_column_matches.append({
                                    "column_name": col_info.get("column_name"),
                                    "column_type": columns_info.get(col_info.get("column_name", ""), {}).get("type", ""),
                                    "purpose": columns_info.get(col_info.get("column_name", ""), {}).get("purpose", "unknown"),
                                    "similarity_score": float(col_info.get("relevance_score", 0.0)),
                                    "confidence": float(col_info.get("confidence", 0.0)),
                                    "reasoning": col_info.get("reasoning", ""),
                                    "usage_suggestion": col_info.get("usage_suggestion", ""),
                                    "analysis_method": "mistral_llm"
                                })
                            
                            # Sort by similarity score
                            table_column_matches.sort(key=lambda x: x["similarity_score"], reverse=True)
                            column_matches[table_name] = table_column_matches[:5]  # Top 5 columns
                            
                    except Exception as e:
                        self.logger.warning(f"Failed to parse column matching LLM response: {str(e)}")
                        column_matches[table_name] = self._fallback_column_matching(entities, columns)
                else:
                    column_matches[table_name] = self._fallback_column_matching(entities, columns)
            
            return column_matches
            
        except Exception as e:
            self.logger.error(f"LLM column matching failed: {str(e)}")
            return {}
    
    def _detect_query_intent_with_llm(self, query: str) -> Dict[str, Any]:
        """Use Mistral LLM to detect query intent"""
        try:
            # Create prompt for intent detection
            prompt = f"""
            Analyze this natural language database query and determine the user's intent. Be intelligent and adaptive.
            
            Query: "{query}"
            
            Return JSON with:
            1. primary_intent: The main intent (list, count, filter, aggregate, search, compare, etc.)
            2. confidence: How confident you are (0.0 to 1.0)
            3. reasoning: Brief explanation of your analysis
            4. query_type: Whether this is a SQL query, document search, or hybrid query
            5. complexity: Simple, moderate, or complex
            6. required_operations: What database operations are needed
            7. business_context: What business question this query is trying to answer
            
            Be intelligent and look for patterns in the query structure and language.
            """
            
            # Get LLM analysis
            llm_response = self.mistral_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model="mistral-small-latest"
            )
            
            if llm_response.get("success"):
                try:
                    content = llm_response.get("content", "{}")
                    json_start = content.find('{')
                    json_end = content.rfind('}') + 1
                    if json_start != -1 and json_end != -1:
                        json_content = content[json_start:json_end]
                        intent = json.loads(json_content)
                        
                        return {
                            "primary_intent": intent.get("primary_intent", "unknown"),
                            "confidence": float(intent.get("confidence", 0.0)),
                            "reasoning": intent.get("reasoning", ""),
                            "query_type": intent.get("query_type", "unknown"),
                            "complexity": intent.get("complexity", "moderate"),
                            "required_operations": intent.get("required_operations", []),
                            "business_context": intent.get("business_context", ""),
                            "analysis_method": "mistral_llm"
                        }
                        
                except Exception as e:
                    self.logger.warning(f"Failed to parse intent detection LLM response: {str(e)}")
            
            # Fallback to simple intent detection
            return self._fallback_intent_detection(query)
            
        except Exception as e:
            self.logger.error(f"LLM intent detection failed: {str(e)}")
            return self._fallback_intent_detection(query)
    
    def _generate_sql_suggestions_with_llm(self, query: str, table_matches: List[Dict], column_matches: Dict, intent: Dict) -> List[Dict[str, Any]]:
        """Use Mistral LLM to generate SQL query suggestions"""
        try:
            if not table_matches:
                return []
            
            primary_table = table_matches[0]
            table_name = primary_table["table_name"]
            table_columns = column_matches.get(table_name, [])
            
            # Create prompt for SQL generation
            prompt = f"""
            Generate SQL query suggestions for this natural language query. Be intelligent and adaptive.
            
            Query: "{query}"
            Primary Table: {table_name}
            Available Columns: {[col.get('column_name') for col in table_columns[:10]]}
            Intent: {intent.get('primary_intent', 'unknown')}
            
            Return JSON with:
            1. sql_suggestions: List of SQL query suggestions
            2. For each suggestion:
               - sql: The SQL query
               - type: Type of query (select, count, aggregate, etc.)
               - confidence: How confident you are (0.0 to 1.0)
               - description: What this query does
               - complexity: Simple, moderate, or complex
               - performance_notes: Any performance considerations
            
            Generate practical, executable SQL queries. Be intelligent about joins, filters, and aggregations.
            """
            
            # Get LLM analysis
            llm_response = self.mistral_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model="mistral-small-latest"
            )
            
            if llm_response.get("success"):
                try:
                    content = llm_response.get("content", "{}")
                    json_start = content.find('{')
                    json_end = content.rfind('}') + 1
                    if json_start != -1 and json_end != -1:
                        json_content = content[json_start:json_end]
                        analysis = json.loads(json_content)
                        
                        suggestions = []
                        for suggestion in analysis.get("sql_suggestions", []):
                            suggestions.append({
                                "sql": suggestion.get("sql", ""),
                                "type": suggestion.get("type", "select"),
                                "confidence": float(suggestion.get("confidence", 0.0)),
                                "description": suggestion.get("description", ""),
                                "complexity": suggestion.get("complexity", "moderate"),
                                "performance_notes": suggestion.get("performance_notes", ""),
                                "analysis_method": "mistral_llm"
                            })
                        
                        return suggestions
                        
                except Exception as e:
                    self.logger.warning(f"Failed to parse SQL generation LLM response: {str(e)}")
            
            # Fallback to simple SQL generation
            return self._fallback_sql_generation(query, table_matches, column_matches, intent)
            
        except Exception as e:
            self.logger.error(f"LLM SQL generation failed: {str(e)}")
            return self._fallback_sql_generation(query, table_matches, column_matches, intent)
    
    def _calculate_overall_confidence_with_llm(self, table_matches: List[Dict], column_matches: Dict) -> float:
        """Calculate overall confidence using LLM analysis"""
        try:
            if not table_matches:
                return 0.0
            
            # Base confidence from best table match
            base_confidence = table_matches[0].get("similarity_score", 0.0)
            
            # Boost confidence if we have good column matches
            column_boost = 0.0
            for table_name, columns in column_matches.items():
                if columns:
                    best_column_score = columns[0].get("similarity_score", 0.0)
                    column_boost += best_column_score * 0.2
            
            total_confidence = min(base_confidence + column_boost, 1.0)
            return total_confidence
            
        except Exception as e:
            self.logger.error(f"Confidence calculation failed: {str(e)}")
            return 0.0
    
    # Fallback methods for when LLM is unavailable
    def _fallback_entity_extraction(self, query: str) -> Dict[str, List[str]]:
        """Fallback entity extraction when LLM is unavailable"""
        import re
        query_lower = query.lower()
        
        return {
            "keywords": re.findall(r'\b\w+\b', query_lower),
            "entities": [],
            "intent": "unknown",
            "filters": [],
            "aggregations": [],
            "sorting": [],
            "business_context": "unknown"
        }
    
    def _fallback_table_matching(self, entities: Dict[str, List[str]], schema: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback table matching when LLM is unavailable"""
        matches = []
        for table_name, table_info in schema.get("tables", {}).items():
            matches.append({
                "table_name": table_name,
                "purpose": table_info.get("purpose", {}).get("primary_purpose", "unknown"),
                "similarity_score": 0.5,
                "confidence": 0.5,
                "reasoning": "Fallback matching",
                "suggested_columns": [],
                "row_count": table_info.get("row_count", 0),
                "analysis_method": "fallback"
            })
        return matches[:3]
    
    def _fallback_column_matching(self, entities: Dict[str, List[str]], columns: Dict) -> List[Dict[str, Any]]:
        """Fallback column matching when LLM is unavailable"""
        matches = []
        for col_name, col_info in columns.items():
            matches.append({
                "column_name": col_name,
                "column_type": col_info.get("type", ""),
                "purpose": col_info.get("purpose", {}).get("primary_purpose", "unknown"),
                "similarity_score": 0.5,
                "confidence": 0.5,
                "reasoning": "Fallback matching",
                "usage_suggestion": "",
                "analysis_method": "fallback"
            })
        return matches[:5]
    
    def _fallback_intent_detection(self, query: str) -> Dict[str, Any]:
        """Fallback intent detection when LLM is unavailable"""
        return {
            "primary_intent": "unknown",
            "confidence": 0.0,
            "reasoning": "LLM analysis unavailable",
            "query_type": "unknown",
            "complexity": "moderate",
            "required_operations": [],
            "business_context": "unknown",
            "analysis_method": "fallback"
        }
    
    def _fallback_sql_generation(self, query: str, table_matches: List[Dict], column_matches: Dict, intent: Dict) -> List[Dict[str, Any]]:
        """Fallback SQL generation when LLM is unavailable"""
        if not table_matches:
            return []
        
        table_name = table_matches[0]["table_name"]
        return [{
            "sql": f"SELECT * FROM {table_name}",
            "type": "select",
            "confidence": 0.5,
            "description": f"Basic query on {table_name}",
            "complexity": "simple",
            "performance_notes": "Basic query",
            "analysis_method": "fallback"
        }]
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    def find_similar_columns(self, term: str, schema: Dict[str, Any], limit: int = 10) -> List[Tuple[str, str, float]]:
        """Find columns similar to a natural language term using LLM"""
        try:
            # Create prompt for column similarity
            prompt = f"""
            Find database columns that are similar to this term. Be intelligent and adaptive.
            
            Search Term: "{term}"
            Available Schema: {json.dumps({name: list(data.get("columns", {}).keys()) for name, data in schema.get("tables", {}).items()}, indent=2)}
            
            Return JSON with:
            1. similar_columns: List of similar columns
            2. For each column:
               - table_name: Name of the table
               - column_name: Name of the column
               - similarity_score: How similar (0.0 to 1.0)
               - reasoning: Why this column is similar
            
            Be intelligent and look for logical connections, not just keyword matches.
            """
            
            # Get LLM analysis
            llm_response = self.mistral_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model="mistral-small-latest"
            )
            
            if llm_response.get("success"):
                try:
                    content = llm_response.get("content", "{}")
                    json_start = content.find('{')
                    json_end = content.rfind('}') + 1
                    if json_start != -1 and json_end != -1:
                        json_content = content[json_start:json_end]
                        analysis = json.loads(json_content)
                        
                        similar_columns = []
                        for col_info in analysis.get("similar_columns", []):
                            similar_columns.append((
                                col_info.get("table_name", ""),
                                col_info.get("column_name", ""),
                                float(col_info.get("similarity_score", 0.0))
                            ))
                        
                        return similar_columns[:limit]
                        
                except Exception as e:
                    self.logger.warning(f"Failed to parse column similarity LLM response: {str(e)}")
            
            # Fallback to simple similarity
            return self._fallback_column_similarity(term, schema, limit)
            
        except Exception as e:
            self.logger.error(f"LLM column similarity failed: {str(e)}")
            return self._fallback_column_similarity(term, schema, limit)
    
    def _fallback_column_similarity(self, term: str, schema: Dict[str, Any], limit: int) -> List[Tuple[str, str, float]]:
        """Fallback column similarity when LLM is unavailable"""
        from difflib import SequenceMatcher
        
        similar_columns = []
        term_lower = term.lower()
        
        for table_name, table_info in schema.get("tables", {}).items():
            columns = table_info.get("columns", {})
            
            for col_name, col_info in columns.items():
                similarity = SequenceMatcher(None, term_lower, col_name.lower()).ratio()
                if similarity > 0.3:
                    similar_columns.append((table_name, col_name, similarity))
        
        similar_columns.sort(key=lambda x: x[2], reverse=True)
        return similar_columns[:limit]
    
    # Wrapper methods for backward compatibility with tests
    def extract_entities(self, query: str, schema: Dict[str, Any]) -> Dict[str, List[str]]:
        """Wrapper for _extract_entities_with_llm (backward compatibility)"""
        return self._extract_entities_with_llm(query)
    
    def classify_query_intent(self, query: str) -> Dict[str, Any]:
        """Wrapper for _detect_query_intent_with_llm (backward compatibility)"""
        return self._detect_query_intent_with_llm(query)
    
    def generate_sql_query(self, query: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Wrapper for _generate_sql_suggestions_with_llm (backward compatibility)"""
        entities = self._extract_entities_with_llm(query)
        table_matches = self._find_matching_tables_with_llm(entities, schema)
        column_matches = self._find_matching_columns_with_llm(entities, schema, table_matches)
        intent = self._detect_query_intent_with_llm(query)
        
        sql_suggestions = self._generate_sql_suggestions_with_llm(query, table_matches, column_matches, intent)
        
        return {
            "query": query,
            "sql": sql_suggestions.get("primary_sql", ""),
            "confidence": sql_suggestions.get("confidence", 0.0),
            "explanation": sql_suggestions.get("explanation", ""),
            "query_type": intent.get("intent", "unknown")
        }
