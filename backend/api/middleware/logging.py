"""
Logging Middleware
Comprehensive request/response logging and monitoring
"""
import logging
import time
import json
from typing import Dict, Any, Optional
from fastapi import Request, Response
from fastapi.responses import StreamingResponse
import uuid

logger = logging.getLogger(__name__)

class LoggingMiddleware:
    """Logging middleware for request/response monitoring"""
    
    def __init__(self):
        self.logger = logger
    
    async def process_request(self, request: Request) -> Dict[str, Any]:
        """Process incoming request for logging"""
        try:
            # Generate request ID
            request_id = str(uuid.uuid4())
            request.state.request_id = request_id
            
            # Log request details
            request_data = {
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "headers": dict(request.headers),
                "client_ip": self._get_client_ip(request),
                "user_agent": request.headers.get("user-agent", ""),
                "timestamp": time.time()
            }
            
            # Log request
            self.logger.info(f"Request started: {request.method} {request.url.path}", extra=request_data)
            
            return request_data
            
        except Exception as e:
            self.logger.error(f"Request logging error: {str(e)}")
            return {}
    
    async def process_response(self, request: Request, response: Response, request_data: Dict[str, Any]) -> None:
        """Process outgoing response for logging"""
        try:
            # Calculate processing time
            processing_time = time.time() - request_data.get("timestamp", time.time())
            
            # Get response details
            response_data = {
                "request_id": request_data.get("request_id", ""),
                "status_code": response.status_code,
                "processing_time": processing_time,
                "response_size": self._get_response_size(response),
                "timestamp": time.time()
            }
            
            # Log response
            if response.status_code >= 400:
                self.logger.warning(f"Request completed with error: {request.method} {request.url.path}", extra=response_data)
            else:
                self.logger.info(f"Request completed: {request.method} {request.url.path}", extra=response_data)
            
        except Exception as e:
            self.logger.error(f"Response logging error: {str(e)}")
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Check for real IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        return request.client.host if request.client else "unknown"
    
    def _get_response_size(self, response: Response) -> int:
        """Get response size in bytes"""
        try:
            if hasattr(response, 'body'):
                return len(response.body)
            elif isinstance(response, StreamingResponse):
                return 0  # Can't determine size for streaming responses
            else:
                return 0
        except Exception:
            return 0

# Global logging middleware instance
logging_middleware = LoggingMiddleware()
