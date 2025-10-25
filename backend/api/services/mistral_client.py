"""
Mistral AI Client Service
Handles communication with Mistral API for natural language processing
"""
import os
import logging
from typing import List, Dict, Any, Optional
from mistralai import Mistral
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)

logger = logging.getLogger(__name__)

class MistralClient:
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Mistral client
        """
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            raise ValueError("Mistral API key not found. Please set MISTRAL_API_KEY environment variable.")
        
        self.client = Mistral(api_key=self.api_key)
        self.logger = logger
    
    def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "mistral-small-latest",
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Send chat completion request to Mistral API
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model to use (default: mistral-small-latest)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            
        Returns:
            Response from Mistral API
        """
        try:
            self.logger.info(f"Sending chat completion request to Mistral API with model: {model}")
            
            response = self.client.chat.complete(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )
            
            self.logger.info("Successfully received response from Mistral API")
            return {
                "success": True,
                "response": response,
                "content": response.choices[0].message.content if response.choices else "",
                "usage": response.usage.__dict__ if response.usage else {}
            }
            
        except Exception as e:
            self.logger.error(f"Error calling Mistral API: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "content": "",
                "usage": {}
            }
    
    def generate_sql_from_natural_language(
        self, 
        query: str, 
        schema_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate SQL from natural language query using schema information
        
        Args:
            query: Natural language query
            schema_info: Database schema information
            
        Returns:
            Generated SQL and metadata
        """
        system_message = f"""
        You are a SQL expert. Given a natural language query and database schema, generate accurate SQL.
        
        Database Schema:
        {schema_info}
        
        Rules:
        1. Use proper SQL syntax
        2. Include appropriate WHERE clauses
        3. Use JOINs when needed
        4. Add LIMIT for large result sets
        5. Use proper column names from the schema
        """
        
        user_message = f"Convert this natural language query to SQL: {query}"
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        
        return self.chat_completion(messages, temperature=0.1)
    
    def classify_query_type(self, query: str) -> Dict[str, Any]:
        """
        Classify query type (SQL, document, hybrid)
        
        Args:
            query: Natural language query
            
        Returns:
            Classification result
        """
        system_message = """
        You are a query classifier. Classify the user query into one of these types:
        - "sql": Pure database query (e.g., "How many employees do we have?")
        - "document": Document search query (e.g., "Find resumes with Python skills")
        - "hybrid": Both database and document search (e.g., "Python developers earning over 100k")
        
        Respond with only the classification type.
        """
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"Classify this query: {query}"}
        ]
        
        return self.chat_completion(messages, temperature=0.1)
    
    def extract_entities(self, query: str) -> Dict[str, Any]:
        """
        Extract entities and key terms from natural language query
        
        Args:
            query: Natural language query
            
        Returns:
            Extracted entities and terms
        """
        system_message = """
        Extract key entities and terms from the user query that might map to database columns or document content.
        Return a JSON object with:
        - "entities": List of named entities
        - "keywords": List of important keywords
        - "intent": The main intent of the query
        - "filters": Any filtering criteria mentioned
        """
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"Extract entities from: {query}"}
        ]
        
        return self.chat_completion(messages, temperature=0.1)


# Global instance for easy access
_mistral_client = None

def get_mistral_client() -> MistralClient:
    """
    Get or create a global Mistral client instance
    
    Returns:
        MistralClient: Configured Mistral client instance
    """
    global _mistral_client
    if _mistral_client is None:
        _mistral_client = MistralClient()
    return _mistral_client
