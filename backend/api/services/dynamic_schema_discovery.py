"""
Truly Dynamic Schema Discovery Engine
Uses Mistral LLM for intelligent schema analysis without hard-coded patterns
"""
import logging
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
import json
from .mistral_client import MistralClient

logger = logging.getLogger(__name__)

class DynamicSchemaDiscovery:
    """Truly dynamic database schema analysis using Mistral LLM"""
    
    def __init__(self, connection_string: str):
        """
        Initialize dynamic schema discovery
        
        Args:
            connection_string: Database connection string
        """
        self.connection_string = connection_string
        self.engine = None
        self.inspector = None
        self.mistral_client = MistralClient()
        self.logger = logger
        
    def initialize(self):
        """Initialize database connection and inspector"""
        try:
            self.engine = create_engine(
                self.connection_string,
                pool_pre_ping=True,
                echo=False
            )
            self.inspector = inspect(self.engine)
            self.logger.info("Dynamic schema discovery initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize dynamic schema discovery: {str(e)}")
            raise
    
    def discover_schema(self) -> Dict[str, Any]:
        """
        Discover complete database schema using Mistral LLM analysis
        
        Returns:
            Complete schema information with LLM-powered analysis
        """
        try:
            self.logger.info("Starting dynamic schema discovery with Mistral LLM...")
            
            # Get basic database information
            database_info = self._get_database_info()
            
            # Discover all tables dynamically
            tables = self._discover_tables()
            
            # Analyze each table using Mistral LLM
            analyzed_tables = {}
            for table_name in tables:
                self.logger.info(f"Analyzing table with Mistral LLM: {table_name}")
                analyzed_tables[table_name] = self._analyze_table_with_llm(table_name)
            
            # Detect relationships using LLM analysis
            relationships = self._detect_relationships_with_llm(analyzed_tables)
            
            # Generate schema summary using LLM
            schema_summary = self._generate_schema_summary_with_llm(analyzed_tables, relationships)
            
            schema_data = {
                "database_info": database_info,
                "tables": analyzed_tables,
                "relationships": relationships,
                "summary": schema_summary,
                "discovered_at": datetime.utcnow().isoformat(),
                "connection_hash": self._generate_connection_hash(),
                "analysis_method": "mistral_llm_dynamic"
            }
            
            self.logger.info(f"Dynamic schema discovery completed for {len(tables)} tables")
            return schema_data
            
        except Exception as e:
            self.logger.error(f"Dynamic schema discovery failed: {str(e)}")
            raise
    
    def _get_database_info(self) -> Dict[str, Any]:
        """Get basic database information"""
        try:
            with self.engine.connect() as conn:
                # Get database version
                version_result = conn.execute(text("SELECT version()"))
                version = version_result.scalar()
                
                # Get database name
                db_name_result = conn.execute(text("SELECT current_database()"))
                db_name = db_name_result.scalar()
                
                return {
                    "name": db_name,
                    "version": version,
                    "dialect": self.engine.dialect.name,
                    "driver": self.engine.dialect.driver
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get database info: {str(e)}")
            return {"error": str(e)}
    
    def _discover_tables(self) -> List[str]:
        """Discover all tables in the database"""
        try:
            tables = self.inspector.get_table_names()
            self.logger.info(f"Discovered {len(tables)} tables dynamically")
            return tables
            
        except Exception as e:
            self.logger.error(f"Failed to discover tables: {str(e)}")
            return []
    
    def _analyze_table_with_llm(self, table_name: str) -> Dict[str, Any]:
        """Analyze table using Mistral LLM for intelligent purpose detection"""
        try:
            # Get table columns dynamically
            columns = self._get_table_columns(table_name)
            
            # Get table constraints dynamically
            constraints = self._get_table_constraints(table_name)
            
            # Get sample data for LLM analysis
            sample_data = self._get_sample_data(table_name)
            
            # Use Mistral LLM to analyze table purpose
            table_purpose = self._analyze_table_purpose_with_llm(table_name, columns, sample_data)
            
            # Use Mistral LLM to analyze columns
            analyzed_columns = self._analyze_columns_with_llm(columns, sample_data)
            
            return {
                "name": table_name,
                "columns": analyzed_columns,
                "constraints": constraints,
                "sample_data": sample_data,
                "purpose": table_purpose,
                "row_count": self._get_table_row_count(table_name),
                "size_estimate": self._estimate_table_size(table_name),
                "analysis_method": "mistral_llm"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to analyze table {table_name} with LLM: {str(e)}")
            return {"name": table_name, "error": str(e)}
    
    def _analyze_table_purpose_with_llm(self, table_name: str, columns: List[Dict], sample_data: List[Dict]) -> Dict[str, Any]:
        """Use Mistral LLM to analyze table purpose intelligently"""
        try:
            # Prepare context for LLM analysis
            column_names = [col.get("name", "") for col in columns]
            column_types = [str(col.get("type", "")) for col in columns]
            
            # Create context for LLM
            context = {
                "table_name": table_name,
                "columns": column_names,
                "column_types": column_types,
                "sample_data": sample_data[:3] if sample_data else []  # Limit sample data
            }
            
            # Create prompt for Mistral LLM
            prompt = f"""
            Analyze this database table and determine its purpose. Be intelligent and adaptive - don't rely on hard-coded patterns.
            
            Table Name: {table_name}
            Columns: {', '.join(column_names)}
            Column Types: {', '.join(column_types)}
            Sample Data: {json.dumps(sample_data[:2], default=str)}
            
            Please analyze and return a JSON response with:
            1. primary_purpose: The most likely purpose (employee, department, salary, performance, document, audit, configuration, or other)
            2. confidence: Confidence score (0.0 to 1.0)
            3. reasoning: Brief explanation of your analysis
            4. alternative_purposes: List of other possible purposes with scores
            5. key_indicators: What specific elements led to this conclusion
            
            Be intelligent and look for patterns in the data, not just names. Consider the actual content and structure.
            """
            
            # Get LLM analysis
            llm_response = self.mistral_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model="mistral-small-latest"
            )
            
            if llm_response.get("success"):
                try:
                    # Parse LLM response
                    content = llm_response.get("content", "{}")
                    # Extract JSON from response
                    json_start = content.find('{')
                    json_end = content.rfind('}') + 1
                    if json_start != -1 and json_end != -1:
                        json_content = content[json_start:json_end]
                        analysis = json.loads(json_content)
                        
                        return {
                            "primary_purpose": analysis.get("primary_purpose", "unknown"),
                            "confidence": float(analysis.get("confidence", 0.0)),
                            "reasoning": analysis.get("reasoning", ""),
                            "alternative_purposes": analysis.get("alternative_purposes", []),
                            "key_indicators": analysis.get("key_indicators", []),
                            "analysis_method": "mistral_llm"
                        }
                except Exception as e:
                    self.logger.warning(f"Failed to parse LLM response: {str(e)}")
            
            # Fallback to simple analysis if LLM fails
            return self._fallback_table_analysis(table_name, columns, sample_data)
            
        except Exception as e:
            self.logger.error(f"LLM table purpose analysis failed: {str(e)}")
            return self._fallback_table_analysis(table_name, columns, sample_data)
    
    def _analyze_columns_with_llm(self, columns: List[Dict], sample_data: List[Dict]) -> Dict[str, Dict[str, Any]]:
        """Use Mistral LLM to analyze columns intelligently"""
        analyzed_columns = {}
        
        for column in columns:
            col_name = column.get("name", "")
            col_type = str(column.get("type", ""))
            
            # Get sample values for this column
            sample_values = []
            for row in sample_data:
                if col_name in row and row[col_name] is not None:
                    sample_values.append(str(row[col_name]))
            
            # Use LLM to analyze column purpose
            column_purpose = self._analyze_column_purpose_with_llm(col_name, col_type, sample_values)
            
            analyzed_columns[col_name] = {
                "name": col_name,
                "type": col_type,
                "nullable": column.get("nullable", True),
                "default": column.get("default"),
                "autoincrement": column.get("autoincrement", False),
                "purpose": column_purpose,
                "sample_values": sample_values[:5],  # Limit sample values
                "analysis_method": "mistral_llm"
            }
        
        return analyzed_columns
    
    def _analyze_column_purpose_with_llm(self, col_name: str, col_type: str, sample_values: List[str]) -> Dict[str, Any]:
        """Use Mistral LLM to analyze column purpose"""
        try:
            # Create prompt for column analysis
            prompt = f"""
            Analyze this database column and determine its purpose. Be intelligent and adaptive.
            
            Column Name: {col_name}
            Column Type: {col_type}
            Sample Values: {sample_values[:5]}
            
            Return JSON with:
            1. primary_purpose: The most likely purpose (identifier, name, email, phone, date, amount, status, address, department, etc.)
            2. confidence: Confidence score (0.0 to 1.0)
            3. reasoning: Brief explanation
            4. data_patterns: What patterns you observed in the data
            
            Be intelligent and look at the actual data patterns, not just the name.
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
                        
                        return {
                            "primary_purpose": analysis.get("primary_purpose", "unknown"),
                            "confidence": float(analysis.get("confidence", 0.0)),
                            "reasoning": analysis.get("reasoning", ""),
                            "data_patterns": analysis.get("data_patterns", []),
                            "analysis_method": "mistral_llm"
                        }
                except Exception as e:
                    self.logger.warning(f"Failed to parse column LLM response: {str(e)}")
            
            # Fallback analysis
            return self._fallback_column_analysis(col_name, col_type, sample_values)
            
        except Exception as e:
            self.logger.error(f"LLM column analysis failed: {str(e)}")
            return self._fallback_column_analysis(col_name, col_type, sample_values)
    
    def _detect_relationships_with_llm(self, tables: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """Use Mistral LLM to detect relationships intelligently"""
        try:
            # Prepare context for relationship analysis
            table_info = {}
            for table_name, table_data in tables.items():
                table_info[table_name] = {
                    "columns": list(table_data.get("columns", {}).keys()),
                    "purpose": table_data.get("purpose", {}).get("primary_purpose", "unknown")
                }
            
            # Create prompt for relationship analysis
            prompt = f"""
            Analyze these database tables and detect relationships between them. Be intelligent and look for logical connections.
            
            Tables: {json.dumps(table_info, indent=2)}
            
            Return JSON with:
            1. explicit_relationships: Foreign key relationships you can identify
            2. implicit_relationships: Logical relationships based on naming and purpose
            3. relationship_strength: How confident you are in each relationship (0.0 to 1.0)
            4. reasoning: Explanation for each relationship
            
            Look for patterns like:
            - Foreign key patterns (table_id columns)
            - Logical connections (employee -> department)
            - Naming conventions that suggest relationships
            - Purpose-based relationships (salary table -> employee table)
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
                        
                        relationships = []
                        
                        # Process explicit relationships
                        for rel in analysis.get("explicit_relationships", []):
                            relationships.append({
                                "type": "explicit",
                                "source_table": rel.get("source_table"),
                                "target_table": rel.get("target_table"),
                                "source_columns": rel.get("source_columns", []),
                                "target_columns": rel.get("target_columns", []),
                                "confidence": float(rel.get("confidence", 0.0)),
                                "reasoning": rel.get("reasoning", ""),
                                "analysis_method": "mistral_llm"
                            })
                        
                        # Process implicit relationships
                        for rel in analysis.get("implicit_relationships", []):
                            relationships.append({
                                "type": "implicit",
                                "source_table": rel.get("source_table"),
                                "target_table": rel.get("target_table"),
                                "source_columns": rel.get("source_columns", []),
                                "target_columns": rel.get("target_columns", []),
                                "confidence": float(rel.get("confidence", 0.0)),
                                "reasoning": rel.get("reasoning", ""),
                                "analysis_method": "mistral_llm"
                            })
                        
                        return relationships
                        
                except Exception as e:
                    self.logger.warning(f"Failed to parse relationship LLM response: {str(e)}")
            
            # Fallback to traditional relationship detection
            return self._fallback_relationship_detection(tables)
            
        except Exception as e:
            self.logger.error(f"LLM relationship detection failed: {str(e)}")
            return self._fallback_relationship_detection(tables)
    
    def _generate_schema_summary_with_llm(self, tables: Dict[str, Dict], relationships: List[Dict]) -> Dict[str, Any]:
        """Use Mistral LLM to generate intelligent schema summary"""
        try:
            # Prepare context for summary
            context = {
                "total_tables": len(tables),
                "total_relationships": len(relationships),
                "table_purposes": {name: data.get("purpose", {}).get("primary_purpose", "unknown") 
                                 for name, data in tables.items()},
                "relationship_types": list(set(rel.get("type", "unknown") for rel in relationships))
            }
            
            # Create prompt for summary
            prompt = f"""
            Generate an intelligent summary of this database schema. Be insightful and provide business context.
            
            Schema Context: {json.dumps(context, indent=2)}
            
            Return JSON with:
            1. business_domain: What business domain this database serves
            2. schema_complexity: Simple, moderate, or complex
            3. key_entities: Main business entities identified
            4. data_relationships: Key relationships between entities
            5. insights: Interesting observations about the schema
            6. recommendations: Suggestions for schema improvements or usage
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
                        
                        return {
                            "total_tables": context["total_tables"],
                            "total_relationships": context["total_relationships"],
                            "business_domain": analysis.get("business_domain", "unknown"),
                            "schema_complexity": analysis.get("schema_complexity", "moderate"),
                            "key_entities": analysis.get("key_entities", []),
                            "data_relationships": analysis.get("data_relationships", []),
                            "insights": analysis.get("insights", []),
                            "recommendations": analysis.get("recommendations", []),
                            "analysis_method": "mistral_llm"
                        }
                        
                except Exception as e:
                    self.logger.warning(f"Failed to parse summary LLM response: {str(e)}")
            
            # Fallback to simple summary
            return self._fallback_schema_summary(tables, relationships)
            
        except Exception as e:
            self.logger.error(f"LLM schema summary failed: {str(e)}")
            return self._fallback_schema_summary(tables, relationships)
    
    # Fallback methods for when LLM is unavailable
    def _fallback_table_analysis(self, table_name: str, columns: List[Dict], sample_data: List[Dict]) -> Dict[str, Any]:
        """Fallback table analysis when LLM is unavailable"""
        return {
            "primary_purpose": "unknown",
            "confidence": 0.0,
            "reasoning": "LLM analysis unavailable",
            "alternative_purposes": [],
            "key_indicators": [],
            "analysis_method": "fallback"
        }
    
    def _fallback_column_analysis(self, col_name: str, col_type: str, sample_values: List[str]) -> Dict[str, Any]:
        """Fallback column analysis when LLM is unavailable"""
        return {
            "primary_purpose": "unknown",
            "confidence": 0.0,
            "reasoning": "LLM analysis unavailable",
            "data_patterns": [],
            "analysis_method": "fallback"
        }
    
    def _fallback_relationship_detection(self, tables: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """Fallback relationship detection when LLM is unavailable"""
        relationships = []
        
        for table_name, table_info in tables.items():
            constraints = table_info.get("constraints", {})
            foreign_keys = constraints.get("foreign_keys", [])
            
            for fk in foreign_keys:
                relationships.append({
                    "type": "explicit",
                    "source_table": table_name,
                    "target_table": fk.get("referred_table"),
                    "source_columns": fk.get("constrained_columns", []),
                    "target_columns": fk.get("referred_columns", []),
                    "confidence": 1.0,
                    "reasoning": "Foreign key constraint detected",
                    "analysis_method": "fallback"
                })
        
        return relationships
    
    def _fallback_schema_summary(self, tables: Dict[str, Dict], relationships: List[Dict]) -> Dict[str, Any]:
        """Fallback schema summary when LLM is unavailable"""
        return {
            "total_tables": len(tables),
            "total_relationships": len(relationships),
            "business_domain": "unknown",
            "schema_complexity": "moderate",
            "key_entities": [],
            "data_relationships": [],
            "insights": [],
            "recommendations": [],
            "analysis_method": "fallback"
        }
    
    # Helper methods (same as original)
    def _get_table_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """Get detailed column information for a table"""
        try:
            return self.inspector.get_columns(table_name)
        except Exception as e:
            self.logger.error(f"Failed to get columns for {table_name}: {str(e)}")
            return []
    
    def _get_table_constraints(self, table_name: str) -> Dict[str, Any]:
        """Get table constraints"""
        try:
            return {
                "primary_keys": self.inspector.get_pk_constraint(table_name),
                "foreign_keys": self.inspector.get_foreign_keys(table_name),
                "unique_constraints": self.inspector.get_unique_constraints(table_name),
                "check_constraints": self.inspector.get_check_constraints(table_name)
            }
        except Exception as e:
            self.logger.error(f"Failed to get constraints for {table_name}: {str(e)}")
            return {}
    
    def _get_sample_data(self, table_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get sample data from table"""
        try:
            with self.engine.connect() as conn:
                query = text(f"SELECT * FROM {table_name} LIMIT {limit}")
                result = conn.execute(query)
                columns = result.keys()
                rows = result.fetchall()
                
                sample_data = []
                for row in rows:
                    sample_data.append(dict(zip(columns, row)))
                
                return sample_data
                
        except Exception as e:
            self.logger.warning(f"Could not get sample data for {table_name}: {str(e)}")
            return []
    
    def _get_table_row_count(self, table_name: str) -> int:
        """Get approximate row count for table"""
        try:
            with self.engine.connect() as conn:
                query = text(f"SELECT COUNT(*) FROM {table_name}")
                result = conn.execute(query)
                return result.scalar()
        except Exception as e:
            self.logger.warning(f"Could not get row count for {table_name}: {str(e)}")
            return 0
    
    def _estimate_table_size(self, table_name: str) -> str:
        """Estimate table size"""
        try:
            with self.engine.connect() as conn:
                query = text(f"SELECT pg_size_pretty(pg_total_relation_size('{table_name}')) as size")
                result = conn.execute(query)
                return result.scalar()
        except Exception as e:
            self.logger.warning(f"Could not estimate size for {table_name}: {str(e)}")
            return "Unknown"
    
    def _generate_connection_hash(self) -> str:
        """Generate hash for connection string caching"""
        return hashlib.sha256(self.connection_string.encode()).hexdigest()
    
    def close(self):
        """Close database connections"""
        if self.engine:
            self.engine.dispose()
