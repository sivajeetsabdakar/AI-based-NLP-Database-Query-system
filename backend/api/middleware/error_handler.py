"""
Error Handling Middleware
Comprehensive error handling and response formatting
"""
import logging
import traceback
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import time

logger = logging.getLogger(__name__)

class ErrorHandlerMiddleware:
    """Error handling middleware for comprehensive error management"""
    
    def __init__(self):
        self.logger = logger
    
    async def handle_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """Handle exceptions and return appropriate error responses"""
        try:
            # Get request ID if available
            request_id = getattr(request.state, 'request_id', 'unknown')
            
            # Log the exception
            self.logger.error(f"Exception occurred: {str(exc)}", extra={
                "request_id": request_id,
                "exception_type": type(exc).__name__,
                "traceback": traceback.format_exc()
            })
            
            # Handle specific exception types
            if isinstance(exc, HTTPException):
                return self._handle_http_exception(exc, request_id)
            elif isinstance(exc, RequestValidationError):
                return self._handle_validation_error(exc, request_id)
            elif isinstance(exc, ValidationError):
                return self._handle_pydantic_validation_error(exc, request_id)
            elif isinstance(exc, ValueError):
                return self._handle_value_error(exc, request_id)
            elif isinstance(exc, KeyError):
                return self._handle_key_error(exc, request_id)
            elif isinstance(exc, AttributeError):
                return self._handle_attribute_error(exc, request_id)
            else:
                return self._handle_generic_error(exc, request_id)
                
        except Exception as e:
            # Fallback error handling
            self.logger.critical(f"Error handler failed: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "code": "INTERNAL_ERROR",
                    "request_id": request_id,
                    "timestamp": time.time()
                }
            )
    
    def _handle_http_exception(self, exc: HTTPException, request_id: str) -> JSONResponse:
        """Handle HTTP exceptions"""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "code": "HTTP_ERROR",
                "request_id": request_id,
                "timestamp": time.time()
            }
        )
    
    def _handle_validation_error(self, exc: RequestValidationError, request_id: str) -> JSONResponse:
        """Handle request validation errors"""
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation error",
                "code": "VALIDATION_ERROR",
                "details": exc.errors(),
                "request_id": request_id,
                "timestamp": time.time()
            }
        )
    
    def _handle_pydantic_validation_error(self, exc: ValidationError, request_id: str) -> JSONResponse:
        """Handle Pydantic validation errors"""
        return JSONResponse(
            status_code=422,
            content={
                "error": "Data validation error",
                "code": "DATA_VALIDATION_ERROR",
                "details": exc.errors(),
                "request_id": request_id,
                "timestamp": time.time()
            }
        )
    
    def _handle_value_error(self, exc: ValueError, request_id: str) -> JSONResponse:
        """Handle value errors"""
        return JSONResponse(
            status_code=400,
            content={
                "error": "Invalid value",
                "code": "VALUE_ERROR",
                "message": str(exc),
                "request_id": request_id,
                "timestamp": time.time()
            }
        )
    
    def _handle_key_error(self, exc: KeyError, request_id: str) -> JSONResponse:
        """Handle key errors"""
        return JSONResponse(
            status_code=400,
            content={
                "error": "Missing required field",
                "code": "KEY_ERROR",
                "message": f"Missing key: {str(exc)}",
                "request_id": request_id,
                "timestamp": time.time()
            }
        )
    
    def _handle_attribute_error(self, exc: AttributeError, request_id: str) -> JSONResponse:
        """Handle attribute errors"""
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "code": "ATTRIBUTE_ERROR",
                "message": "Service configuration error",
                "request_id": request_id,
                "timestamp": time.time()
            }
        )
    
    def _handle_generic_error(self, exc: Exception, request_id: str) -> JSONResponse:
        """Handle generic errors"""
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "request_id": request_id,
                "timestamp": time.time()
            }
        )

# Global error handler middleware instance
error_handler_middleware = ErrorHandlerMiddleware()
