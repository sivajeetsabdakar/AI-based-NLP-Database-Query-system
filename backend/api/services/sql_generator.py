"""
Natural Language to SQL Generation
Convert natural language queries to SQL using Mistral API and schema mapping
"""
import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json

from .mistral_client import get_mistral_client
from .database_utils import get_database_utils
from .redis_service import get_redis_service
from .schema_service import get_schema_service

logger = logging.getLogger(__name__)

class SQLGenerator:
    """Natural language to SQL generation using Mistral API"""
    
    def __init__(self):
        self.logger = logger
        self.mistral_client = None
        self.db_utils = None
        self.redis_service = None
        self.schema_service = None
        
        # SQL generation patterns
        self.sql_patterns = {
            "count": {
                "patterns": ["how many", "count", "total", "number of"],
                "template": "SELECT COUNT(*) FROM {table} WHERE {conditions}"
            },
            "list": {
                "patterns": ["list", "show", "display", "get", "find"],
                "template": "SELECT {columns} FROM {table} WHERE {conditions}"
            },
            "aggregate": {
                "patterns": ["average", "sum", "max", "min", "avg"],
                "template": "SELECT {function}({column}) FROM {table} WHERE {conditions}"
            },
            "group_by": {
                "patterns": ["group by", "by department", "by position", "per"],
                "template": "SELECT {group_column}, {function}({column}) FROM {table} WHERE {conditions} GROUP BY {group_column}"
            }
        }
        
        # Common SQL functions
        self.sql_functions = {
            "count": "COUNT",
            "sum": "SUM", 
            "average": "AVG",
            "max": "MAX",
            "min": "MIN"
        }
        
        # SQL security patterns to avoid
        self.dangerous_patterns = [
            "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE",
            "TRUNCATE", "EXEC", "EXECUTE", "UNION", "INFORMATION_SCHEMA"
        ]
    
    def initialize(self):
        """Initialize the SQL generator"""
        try:
            # Initialize services
            self.mistral_client = get_mistral_client()
            self.db_utils = get_database_utils()
            self.redis_service = get_redis_service()
            self.schema_service = get_schema_service()
            
            self.logger.info("SQL generator initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize SQL generator: {str(e)}")
            raise
    
    def generate_sql(self, query: str, schema_info: Optional[Dict[str, Any]] = None, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate SQL from natural language query using Mistral API
        
        Args:
            query: Natural language query
            schema_info: Optional schema information
            user_context: Optional user context
            
        Returns:
            SQL generation result with query, confidence, and metadata
        """
        try:
            self.logger.info(f"Generating SQL for query: {query[:100]}...")
            
            # Check cache first
            cache_key = f"sql_generation:{hash(query)}"
            cached_result = self._get_cached_sql(cache_key)
            if cached_result:
                self.logger.info("Using cached SQL generation result")
                return cached_result
            
            # Get schema information if not provided
            if not schema_info:
                schema_info = self._get_schema_info()
            
            # Generate SQL using Mistral API
            sql_result = self._generate_sql_with_mistral(query, schema_info, user_context)
            
            # Validate and optimize SQL
            validated_result = self._validate_and_optimize_sql(sql_result, schema_info)
            
            # Cache result
            self._cache_sql(cache_key, validated_result)
            
            self.logger.info(f"SQL generated successfully: {validated_result['sql'][:100]}...")
            
            return validated_result
            
        except Exception as e:
            self.logger.error(f"SQL generation failed: {str(e)}")
            return {
                "query": query,
                "sql": "",
                "confidence": 0.0,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _get_schema_info(self) -> Dict[str, Any]:
        """Get database schema information"""
        try:
            if self.schema_service:
                # Get schema from schema service
                schema_info = self.schema_service.get_schema_info()
                return schema_info
            else:
                # Fallback to basic schema info
                return self._get_basic_schema_info()
                
        except Exception as e:
            self.logger.error(f"Failed to get schema info: {str(e)}")
            return self._get_basic_schema_info()
    
    def _get_basic_schema_info(self) -> Dict[str, Any]:
        """Get basic schema information as fallback"""
        return {
            "tables": {
                "employees": {
                    "columns": ["id", "name", "email", "department", "position", "salary", "hire_date"],
                    "description": "Employee information table"
                },
                "departments": {
                    "columns": ["id", "name", "description", "manager_id"],
                    "description": "Department information table"
                }
            },
            "relationships": [
                {"from": "employees.department", "to": "departments.id", "type": "foreign_key"}
            ]
        }
    
    def _generate_sql_with_mistral(self, query: str, schema_info: Dict[str, Any], user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate SQL using Mistral API"""
        try:
            if not self.mistral_client:
                raise ValueError("Mistral client not initialized")
            
            # Create SQL generation prompt
            prompt = self._create_sql_generation_prompt(query, schema_info, user_context)
            
            # Get Mistral API response
            response = self.mistral_client.generate_response(prompt)
            
            # Parse response
            sql_result = self._parse_mistral_sql_response(response)
            
            return sql_result
            
        except Exception as e:
            self.logger.error(f"Mistral API SQL generation failed: {str(e)}")
            # Fallback to pattern-based SQL generation
            return self._fallback_sql_generation(query, schema_info)
    
    def _create_sql_generation_prompt(self, query: str, schema_info: Dict[str, Any], user_context: Optional[Dict[str, Any]] = None) -> str:
        """Create prompt for Mistral API SQL generation"""
        prompt = f"""
You are an expert SQL generator for an employee database system. Convert the following natural language query to SQL.

Database Schema:
{json.dumps(schema_info, indent=2)}

Natural Language Query: "{query}"

Requirements:
1. Generate valid SQL that follows the schema
2. Use appropriate table and column names from the schema
3. Include proper WHERE clauses for filtering
4. Use appropriate SQL functions (COUNT, SUM, AVG, MAX, MIN)
5. Include proper JOINs when needed
6. Ensure the query is safe and read-only
7. Do not include DROP, DELETE, UPDATE, INSERT, or other dangerous operations

Please respond with a JSON object containing:
- sql: The generated SQL query
- confidence: Float between 0.0 and 1.0 indicating generation confidence
- reasoning: Brief explanation of the SQL generation
- tables_used: List of tables used in the query
- columns_used: List of columns used in the query
- query_type: Type of query (SELECT, COUNT, AGGREGATE, etc.)

Examples:
- "How many employees do we have?" → SELECT COUNT(*) FROM employees
- "Show me all employees in Engineering" → SELECT * FROM employees WHERE department = 'Engineering'
- "Average salary by department" → SELECT department, AVG(salary) FROM employees GROUP BY department

Respond only with valid JSON.
"""
        
        if user_context:
            prompt += f"\nUser Context: {json.dumps(user_context)}"
        
        return prompt
    
    def _parse_mistral_sql_response(self, response: str) -> Dict[str, Any]:
        """Parse Mistral API response for SQL generation"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                result = json.loads(json_str)
                
                # Validate required fields
                required_fields = ['sql', 'confidence', 'reasoning', 'tables_used', 'columns_used', 'query_type']
                for field in required_fields:
                    if field not in result:
                        result[field] = self._get_default_sql_value(field)
                
                return result
            else:
                # Fallback parsing
                return self._parse_sql_text_response(response)
                
        except Exception as e:
            self.logger.error(f"Failed to parse Mistral SQL response: {str(e)}")
            return self._get_default_sql_result()
    
    def _parse_sql_text_response(self, response: str) -> Dict[str, Any]:
        """Parse text response when JSON parsing fails"""
        try:
            # Extract SQL query
            sql_query = ""
            sql_match = re.search(r'SELECT.*?(?=\n|$)', response, re.IGNORECASE | re.DOTALL)
            if sql_match:
                sql_query = sql_match.group().strip()
            
            # Extract confidence
            confidence = 0.5
            confidence_match = re.search(r'confidence[:\s]*([0-9.]+)', response, re.IGNORECASE)
            if confidence_match:
                confidence = float(confidence_match.group(1))
            
            # Extract tables used
            tables_used = []
            table_match = re.search(r'FROM\s+(\w+)', sql_query, re.IGNORECASE)
            if table_match:
                tables_used.append(table_match.group(1))
            
            # Extract columns used
            columns_used = []
            column_matches = re.findall(r'SELECT\s+(.*?)\s+FROM', sql_query, re.IGNORECASE)
            if column_matches:
                columns = [col.strip() for col in column_matches[0].split(',')]
                columns_used.extend(columns)
            
            return {
                "sql": sql_query,
                "confidence": confidence,
                "reasoning": response[:200] + "..." if len(response) > 200 else response,
                "tables_used": tables_used,
                "columns_used": columns_used,
                "query_type": "SELECT"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to parse SQL text response: {str(e)}")
            return self._get_default_sql_result()
    
    def _get_default_sql_result(self) -> Dict[str, Any]:
        """Get default SQL result when parsing fails"""
        return {
            "sql": "",
            "confidence": 0.0,
            "reasoning": "Failed to parse response",
            "tables_used": [],
            "columns_used": [],
            "query_type": "SELECT"
        }
    
    def _get_default_sql_value(self, field: str) -> Any:
        """Get default value for missing SQL field"""
        defaults = {
            "sql": "",
            "confidence": 0.5,
            "reasoning": "No reasoning provided",
            "tables_used": [],
            "columns_used": [],
            "query_type": "SELECT"
        }
        return defaults.get(field, None)
    
    def _fallback_sql_generation(self, query: str, schema_info: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback pattern-based SQL generation when Mistral API fails"""
        try:
            query_lower = query.lower()
            
            # Determine query type
            query_type = "SELECT"
            if any(pattern in query_lower for pattern in ["how many", "count", "total", "number of"]):
                query_type = "COUNT"
            elif any(pattern in query_lower for pattern in ["average", "sum", "max", "min", "avg"]):
                query_type = "AGGREGATE"
            elif any(pattern in query_lower for pattern in ["group by", "by department", "by position"]):
                query_type = "GROUP_BY"
            
            # Generate basic SQL
            sql_query = self._generate_basic_sql(query, schema_info, query_type)
            
            # Extract tables and columns
            tables_used = self._extract_tables_from_sql(sql_query)
            columns_used = self._extract_columns_from_sql(sql_query)
            
            return {
                "sql": sql_query,
                "confidence": 0.6,
                "reasoning": f"Pattern-based SQL generation for {query_type} query",
                "tables_used": tables_used,
                "columns_used": columns_used,
                "query_type": query_type
            }
            
        except Exception as e:
            self.logger.error(f"Fallback SQL generation failed: {str(e)}")
            return self._get_default_sql_result()
    
    def _generate_basic_sql(self, query: str, schema_info: Dict[str, Any], query_type: str) -> str:
        """Generate basic SQL query"""
        try:
            # Get available tables
            tables = list(schema_info.get("tables", {}).keys())
            if not tables:
                return "SELECT 1"  # Fallback query
            
            # Use first table as default
            main_table = tables[0]
            
            if query_type == "COUNT":
                return f"SELECT COUNT(*) FROM {main_table}"
            elif query_type == "AGGREGATE":
                # Try to find a numeric column
                numeric_columns = self._find_numeric_columns(schema_info)
                if numeric_columns:
                    return f"SELECT AVG({numeric_columns[0]}) FROM {main_table}"
                else:
                    return f"SELECT COUNT(*) FROM {main_table}"
            else:
                return f"SELECT * FROM {main_table} LIMIT 10"
                
        except Exception as e:
            self.logger.error(f"Basic SQL generation failed: {str(e)}")
            return "SELECT 1"
    
    def _find_numeric_columns(self, schema_info: Dict[str, Any]) -> List[str]:
        """Find numeric columns in schema"""
        numeric_columns = []
        for table_name, table_info in schema_info.get("tables", {}).items():
            for column in table_info.get("columns", []):
                if any(numeric_type in column.lower() for numeric_type in ["salary", "id", "count", "number", "amount"]):
                    numeric_columns.append(f"{table_name}.{column}")
        return numeric_columns
    
    def _extract_tables_from_sql(self, sql: str) -> List[str]:
        """Extract table names from SQL query"""
        try:
            tables = []
            # Find FROM clause
            from_match = re.search(r'FROM\s+(\w+)', sql, re.IGNORECASE)
            if from_match:
                tables.append(from_match.group(1))
            
            # Find JOIN clauses
            join_matches = re.findall(r'JOIN\s+(\w+)', sql, re.IGNORECASE)
            tables.extend(join_matches)
            
            return tables
            
        except Exception as e:
            self.logger.error(f"Failed to extract tables from SQL: {str(e)}")
            return []
    
    def _extract_columns_from_sql(self, sql: str) -> List[str]:
        """Extract column names from SQL query"""
        try:
            columns = []
            # Find SELECT clause
            select_match = re.search(r'SELECT\s+(.*?)\s+FROM', sql, re.IGNORECASE)
            if select_match:
                select_clause = select_match.group(1)
                if select_clause != "*":
                    columns = [col.strip() for col in select_clause.split(',')]
            
            return columns
            
        except Exception as e:
            self.logger.error(f"Failed to extract columns from SQL: {str(e)}")
            return []
    
    def _validate_and_optimize_sql(self, sql_result: Dict[str, Any], schema_info: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and optimize generated SQL"""
        try:
            sql_query = sql_result.get("sql", "")
            
            # Security validation
            security_result = self._validate_sql_security(sql_query)
            if not security_result["safe"]:
                sql_result["error"] = f"SQL security validation failed: {security_result['reason']}"
                sql_result["confidence"] = 0.0
                return sql_result
            
            # Schema validation
            schema_result = self._validate_sql_schema(sql_query, schema_info)
            if not schema_result["valid"]:
                sql_result["error"] = f"SQL schema validation failed: {schema_result['reason']}"
                sql_result["confidence"] = max(0.0, sql_result.get("confidence", 0.5) - 0.2)
            
            # Add validation results
            sql_result["security_valid"] = security_result["safe"]
            sql_result["schema_valid"] = schema_result["valid"]
            sql_result["validation_errors"] = schema_result.get("errors", [])
            
            # Optimize SQL if needed
            optimized_sql = self._optimize_sql(sql_query)
            if optimized_sql != sql_query:
                sql_result["sql"] = optimized_sql
                sql_result["optimized"] = True
            
            return sql_result
            
        except Exception as e:
            self.logger.error(f"SQL validation and optimization failed: {str(e)}")
            sql_result["error"] = str(e)
            return sql_result
    
    def _validate_sql_security(self, sql: str) -> Dict[str, Any]:
        """Validate SQL for security issues"""
        try:
            sql_upper = sql.upper()
            
            # Check for dangerous patterns
            for pattern in self.dangerous_patterns:
                if pattern in sql_upper:
                    return {
                        "safe": False,
                        "reason": f"Dangerous SQL pattern detected: {pattern}"
                    }
            
            # Check for SQL injection patterns
            injection_patterns = [
                r"'.*'.*'.*",  # Quote manipulation
                r"--",  # SQL comments
                r"\/\*.*\*\/",  # Block comments
                r"UNION.*SELECT",  # Union attacks
                r"OR.*1.*=.*1",  # Always true conditions
            ]
            
            for pattern in injection_patterns:
                if re.search(pattern, sql, re.IGNORECASE):
                    return {
                        "safe": False,
                        "reason": f"Potential SQL injection pattern detected: {pattern}"
                    }
            
            return {"safe": True, "reason": "SQL appears safe"}
            
        except Exception as e:
            self.logger.error(f"SQL security validation failed: {str(e)}")
            return {"safe": False, "reason": f"Security validation error: {str(e)}"}
    
    def _validate_sql_schema(self, sql: str, schema_info: Dict[str, Any]) -> Dict[str, Any]:
        """Validate SQL against database schema"""
        try:
            errors = []
            
            # Extract tables from SQL
            tables_used = self._extract_tables_from_sql(sql)
            available_tables = list(schema_info.get("tables", {}).keys())
            
            # Check if tables exist
            for table in tables_used:
                if table not in available_tables:
                    errors.append(f"Table '{table}' not found in schema")
            
            # Extract columns from SQL
            columns_used = self._extract_columns_from_sql(sql)
            
            # Check if columns exist in their tables
            for column in columns_used:
                if "." in column:
                    table, col = column.split(".", 1)
                    if table in schema_info.get("tables", {}):
                        available_columns = schema_info["tables"][table].get("columns", [])
                        if col not in available_columns:
                            errors.append(f"Column '{col}' not found in table '{table}'")
            
            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "reason": "Schema validation completed"
            }
            
        except Exception as e:
            self.logger.error(f"SQL schema validation failed: {str(e)}")
            return {
                "valid": False,
                "errors": [f"Schema validation error: {str(e)}"],
                "reason": "Schema validation failed"
            }
    
    def _optimize_sql(self, sql: str) -> str:
        """Optimize SQL query for better performance"""
        try:
            # Basic optimizations
            optimized = sql.strip()
            
            # Remove extra whitespace
            optimized = re.sub(r'\s+', ' ', optimized)
            
            # Add LIMIT if not present and it's a SELECT query
            if optimized.upper().startswith('SELECT') and 'LIMIT' not in optimized.upper():
                optimized += ' LIMIT 1000'  # Add reasonable limit
            
            return optimized
            
        except Exception as e:
            self.logger.error(f"SQL optimization failed: {str(e)}")
            return sql
    
    def _get_cached_sql(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached SQL generation result"""
        try:
            if not self.redis_service:
                return None
            
            cached_result = self.redis_service.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get cached SQL: {str(e)}")
            return None
    
    def _cache_sql(self, cache_key: str, result: Dict[str, Any]):
        """Cache SQL generation result"""
        try:
            if not self.redis_service:
                return
            
            # Cache for 2 hours
            self.redis_service.set(cache_key, json.dumps(result), expire=7200)
            
        except Exception as e:
            self.logger.error(f"Failed to cache SQL: {str(e)}")
    
    def execute_sql(self, sql: str, limit: int = 1000) -> Dict[str, Any]:
        """Execute SQL query and return results"""
        try:
            if not self.db_utils:
                raise ValueError("Database utils not initialized")
            
            # Add LIMIT if not present
            if 'LIMIT' not in sql.upper():
                sql += f' LIMIT {limit}'
            
            # Execute query
            results = self.db_utils.execute_query(sql)
            
            return {
                "success": True,
                "results": results,
                "row_count": len(results),
                "sql": sql,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"SQL execution failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "sql": sql,
                "timestamp": datetime.utcnow().isoformat()
            }

# Global SQL generator instance
sql_generator: Optional[SQLGenerator] = None

def get_sql_generator() -> SQLGenerator:
    """Get the global SQL generator instance"""
    if sql_generator is None:
        raise RuntimeError("SQL generator not initialized")
    return sql_generator

def initialize_sql_generator() -> SQLGenerator:
    """Initialize the global SQL generator"""
    global sql_generator
    sql_generator = SQLGenerator()
    sql_generator.initialize()
    return sql_generator
