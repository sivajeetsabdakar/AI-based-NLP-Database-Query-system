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
    
    def extract_text_from_pdf_ocr(
        self, 
        file_path: str, 
        model: str = "CX-9",
        bbox_annotation_format: Optional[Dict[str, str]] = None,
        document_annotation_format: Optional[Dict[str, str]] = None,
        id: Optional[str] = None,
        image_limit: Optional[int] = None,
        image_min_size: Optional[int] = None,
        include_image_base64: Optional[bool] = None,
        pages: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Extract text from PDF using Mistral OCR API
        
        Args:
            file_path: Path to the PDF file
            model: OCR model to use (default: CX-9)
            bbox_annotation_format: Format for bbox annotations
            document_annotation_format: Format for document annotations
            id: Optional identifier
            image_limit: Max images to extract
            image_min_size: Minimum height and width of image to extract
            include_image_base64: Include image URLs in response
            pages: Specific pages to process (0-indexed)
            
        Returns:
            OCR result matching the documented API response format
        """
        try:
            self.logger.info(f"Extracting text from PDF using Mistral OCR: {file_path}")
            
            # Read the PDF file as binary data
            with open(file_path, 'rb') as file:
                file_data = file.read()
            
            # Build request parameters according to the correct API documentation
            # For file uploads, we need to use the file_chunk structure
            request_params = {
                "model": model,
                "document": {
                    "type": "file_chunk",
                    "file_chunk": {
                        "data": file_data,
                        "filename": os.path.basename(file_path)
                    }
                }
            }
            
            # Add optional parameters if provided
            if bbox_annotation_format is not None:
                request_params["bbox_annotation_format"] = bbox_annotation_format
            if document_annotation_format is not None:
                request_params["document_annotation_format"] = document_annotation_format
            if id is not None:
                request_params["id"] = id
            if image_limit is not None:
                request_params["image_limit"] = image_limit
            if image_min_size is not None:
                request_params["image_min_size"] = image_min_size
            if include_image_base64 is not None:
                request_params["include_image_base64"] = include_image_base64
            if pages is not None:
                request_params["pages"] = pages
            
            # Use Mistral OCR API with the correct structure
            try:
                # Use the correct API call as per documentation
                response = self.client.ocr.process(
                    model=model,
                    document={
                        "type": "file_chunk",
                        "file_chunk": {
                            "data": file_data,
                            "filename": os.path.basename(file_path)
                        }
                    },
                    bbox_annotation_format=bbox_annotation_format,
                    document_annotation_format=document_annotation_format,
                    id=id,
                    image_limit=image_limit,
                    image_min_size=image_min_size,
                    include_image_base64=include_image_base64,
                    pages=pages
                )
            except Exception as api_error:
                # If the API structure is wrong, try alternative approach
                self.logger.warning(f"Primary OCR API failed: {str(api_error)}, trying alternative approach")
                
                # Alternative: Try with different document structure
                try:
                    response = self.client.ocr.process(
                        model=model,
                        document=file_data,  # Send file data directly
                        bbox_annotation_format=bbox_annotation_format,
                        document_annotation_format=document_annotation_format,
                        id=id,
                        image_limit=image_limit,
                        image_min_size=image_min_size,
                        include_image_base64=include_image_base64,
                        pages=pages
                    )
                except Exception as alt_error:
                    self.logger.error(f"Alternative OCR API also failed: {str(alt_error)}")
                    raise api_error  # Re-raise the original error
            
            # Extract text from all pages
            extracted_text = ""
            if hasattr(response, 'pages') and response.pages:
                for page in response.pages:
                    if hasattr(page, 'markdown') and page.markdown:
                        extracted_text += page.markdown + "\n\n"
            
            self.logger.info(f"Successfully extracted text from PDF using Mistral OCR")
            
            # Return response in documented format
            return {
                "success": True,
                "document_annotation": getattr(response, 'document_annotation', None),
                "model": getattr(response, 'model', model),
                "pages": getattr(response, 'pages', []),
                "usage_info": getattr(response, 'usage_info', {}),
                "extracted_text": extracted_text.strip(),  # Keep for backward compatibility
                "raw_response": response
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting text from PDF using Mistral OCR: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "document_annotation": None,
                "model": model,
                "pages": [],
                "usage_info": {},
                "extracted_text": ""
            }
    
    def extract_text_from_image_ocr(
        self, 
        image_path: str, 
        model: str = "CX-9",
        bbox_annotation_format: Optional[Dict[str, str]] = None,
        document_annotation_format: Optional[Dict[str, str]] = None,
        id: Optional[str] = None,
        image_limit: Optional[int] = None,
        image_min_size: Optional[int] = None,
        include_image_base64: Optional[bool] = None,
        pages: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Extract text from image using Mistral OCR API
        
        Args:
            image_path: Path to the image file
            model: OCR model to use (default: CX-9)
            bbox_annotation_format: Format for bbox annotations
            document_annotation_format: Format for document annotations
            id: Optional identifier
            image_limit: Max images to extract
            image_min_size: Minimum height and width of image to extract
            include_image_base64: Include image URLs in response
            pages: Specific pages to process (0-indexed)
            
        Returns:
            OCR result matching the documented API response format
        """
        try:
            self.logger.info(f"Extracting text from image using Mistral OCR: {image_path}")
            
            # Read the image file as binary data
            with open(image_path, 'rb') as file:
                image_data = file.read()
            
            # Build request parameters according to the correct API documentation
            # For image file uploads, we need to use the file_chunk structure
            request_params = {
                "model": model,
                "document": {
                    "type": "file_chunk",
                    "file_chunk": {
                        "data": image_data,
                        "filename": os.path.basename(image_path)
                    }
                }
            }
            
            # Add optional parameters if provided
            if bbox_annotation_format is not None:
                request_params["bbox_annotation_format"] = bbox_annotation_format
            if document_annotation_format is not None:
                request_params["document_annotation_format"] = document_annotation_format
            if id is not None:
                request_params["id"] = id
            if image_limit is not None:
                request_params["image_limit"] = image_limit
            if image_min_size is not None:
                request_params["image_min_size"] = image_min_size
            if include_image_base64 is not None:
                request_params["include_image_base64"] = include_image_base64
            if pages is not None:
                request_params["pages"] = pages
            
            # Use Mistral OCR API with the correct structure
            try:
                # Use the correct API call as per documentation
                response = self.client.ocr.process(
                    model=model,
                    document={
                        "type": "file_chunk",
                        "file_chunk": {
                            "data": image_data,
                            "filename": os.path.basename(image_path)
                        }
                    },
                    bbox_annotation_format=bbox_annotation_format,
                    document_annotation_format=document_annotation_format,
                    id=id,
                    image_limit=image_limit,
                    image_min_size=image_min_size,
                    include_image_base64=include_image_base64,
                    pages=pages
                )
            except Exception as api_error:
                # If the API structure is wrong, try alternative approach
                self.logger.warning(f"Primary OCR API failed: {str(api_error)}, trying alternative approach")
                
                # Alternative: Try with different document structure
                try:
                    response = self.client.ocr.process(
                        model=model,
                        document=image_data,  # Send image data directly
                        bbox_annotation_format=bbox_annotation_format,
                        document_annotation_format=document_annotation_format,
                        id=id,
                        image_limit=image_limit,
                        image_min_size=image_min_size,
                        include_image_base64=include_image_base64,
                        pages=pages
                    )
                except Exception as alt_error:
                    self.logger.error(f"Alternative OCR API also failed: {str(alt_error)}")
                    raise api_error  # Re-raise the original error
            
            # Extract text from all pages
            extracted_text = ""
            if hasattr(response, 'pages') and response.pages:
                for page in response.pages:
                    if hasattr(page, 'markdown') and page.markdown:
                        extracted_text += page.markdown + "\n\n"
            
            self.logger.info(f"Successfully extracted text from image using Mistral OCR")
            
            # Return response in documented format
            return {
                "success": True,
                "document_annotation": getattr(response, 'document_annotation', None),
                "model": getattr(response, 'model', model),
                "pages": getattr(response, 'pages', []),
                "usage_info": getattr(response, 'usage_info', {}),
                "extracted_text": extracted_text.strip(),  # Keep for backward compatibility
                "raw_response": response
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting text from image using Mistral OCR: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "document_annotation": None,
                "model": model,
                "pages": [],
                "usage_info": {},
                "extracted_text": ""
            }
    
    def extract_text_from_url_ocr(
        self,
        url: str,
        document_type: str = "image_url",  # "image_url" or "document_url"
        model: str = "CX-9",
        bbox_annotation_format: Optional[Dict[str, str]] = None,
        document_annotation_format: Optional[Dict[str, str]] = None,
        id: Optional[str] = None,
        image_limit: Optional[int] = None,
        image_min_size: Optional[int] = None,
        include_image_base64: Optional[bool] = None,
        pages: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Extract text from URL using Mistral OCR API
        
        Args:
            url: URL to the document/image
            document_type: Type of document ("image_url" or "document_url")
            model: OCR model to use (default: CX-9)
            bbox_annotation_format: Format for bbox annotations
            document_annotation_format: Format for document annotations
            id: Optional identifier
            image_limit: Max images to extract
            image_min_size: Minimum height and width of image to extract
            include_image_base64: Include image URLs in response
            pages: Specific pages to process (0-indexed)
            
        Returns:
            OCR result matching the documented API response format
        """
        try:
            self.logger.info(f"Extracting text from URL using Mistral OCR: {url}")
            
            # Build request parameters according to the correct API documentation
            # For URLs, we need to use the correct structure based on document type
            if document_type == "image_url":
                document_structure = {
                    "type": "image_url",
                    "image_url": {
                        "url": url
                    }
                }
            elif document_type == "document_url":
                document_structure = {
                    "type": "document_url", 
                    "document_url": {
                        "url": url
                    }
                }
            else:
                # Default to image_url if unknown
                document_structure = {
                    "type": "image_url",
                    "image_url": {
                        "url": url
                    }
                }
            
            request_params = {
                "model": model,
                "document": document_structure
            }
            
            # Add optional parameters if provided
            if bbox_annotation_format is not None:
                request_params["bbox_annotation_format"] = bbox_annotation_format
            if document_annotation_format is not None:
                request_params["document_annotation_format"] = document_annotation_format
            if id is not None:
                request_params["id"] = id
            if image_limit is not None:
                request_params["image_limit"] = image_limit
            if image_min_size is not None:
                request_params["image_min_size"] = image_min_size
            if include_image_base64 is not None:
                request_params["include_image_base64"] = include_image_base64
            if pages is not None:
                request_params["pages"] = pages
            
            # Use Mistral OCR API with the correct structure
            try:
                # Use the correct API call as per documentation
                response = self.client.ocr.process(
                    model=model,
                    document=document_structure,
                    bbox_annotation_format=bbox_annotation_format,
                    document_annotation_format=document_annotation_format,
                    id=id,
                    image_limit=image_limit,
                    image_min_size=image_min_size,
                    include_image_base64=include_image_base64,
                    pages=pages
                )
            except Exception as api_error:
                # If the API structure is wrong, try alternative approach
                self.logger.warning(f"Primary OCR API failed: {str(api_error)}, trying alternative approach")
                
                # Alternative: Try with different document structure
                try:
                    response = self.client.ocr.process(
                        model=model,
                        document={"type": document_type, "url": url},  # Simplified structure
                        bbox_annotation_format=bbox_annotation_format,
                        document_annotation_format=document_annotation_format,
                        id=id,
                        image_limit=image_limit,
                        image_min_size=image_min_size,
                        include_image_base64=include_image_base64,
                        pages=pages
                    )
                except Exception as alt_error:
                    self.logger.error(f"Alternative OCR API also failed: {str(alt_error)}")
                    raise api_error  # Re-raise the original error
            
            # Extract text from all pages
            extracted_text = ""
            if hasattr(response, 'pages') and response.pages:
                for page in response.pages:
                    if hasattr(page, 'markdown') and page.markdown:
                        extracted_text += page.markdown + "\n\n"
            
            self.logger.info(f"Successfully extracted text from URL using Mistral OCR")
            
            # Return response in documented format
            return {
                "success": True,
                "document_annotation": getattr(response, 'document_annotation', None),
                "model": getattr(response, 'model', model),
                "pages": getattr(response, 'pages', []),
                "usage_info": getattr(response, 'usage_info', {}),
                "extracted_text": extracted_text.strip(),  # Keep for backward compatibility
                "raw_response": response
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting text from URL using Mistral OCR: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "document_annotation": None,
                "model": model,
                "pages": [],
                "usage_info": {},
                "extracted_text": ""
            }
    
    def generate_response(self, prompt: str, model: str = "mistral-small-latest", temperature: float = 0.2) -> Dict[str, Any]:
        """
        Generate response from a simple prompt (backward compatibility method)
        
        Args:
            prompt: Input prompt
            model: Model to use
            temperature: Sampling temperature
            
        Returns:
            Generated response
        """
        messages = [{"role": "user", "content": prompt}]
        return self.chat_completion(messages, model=model, temperature=temperature)


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
