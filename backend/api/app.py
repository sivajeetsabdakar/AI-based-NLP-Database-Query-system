"""
Main FastAPI Application
Comprehensive API application with middleware, routing, and documentation
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import uvicorn
import time

from config import setup_logging, settings
from api.middleware import security_middleware, logging_middleware, error_handler_middleware
from api.endpoints import schema_endpoints, document_endpoints, query_endpoints

# Setup logging
logger = setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting API application...")
    yield
    # Shutdown
    logger.info("Shutting down API application...")

# Create FastAPI application
app = FastAPI(
    title="Ekam NLP Query Engine API",
    description="Natural Language Query Engine for Employee Database with Dynamic Schema Discovery",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Custom middleware for security, logging, and error handling
@app.middleware("http")
async def security_middleware_handler(request: Request, call_next):
    """Security middleware handler"""
    try:
        # Process request through security middleware
        security_response = await security_middleware.process_request(request)
        if security_response:
            return security_response
        
        # Continue to next middleware
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response
        
    except Exception as e:
        logger.error(f"Security middleware error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Security middleware failed", "code": "SECURITY_ERROR"}
        )

@app.middleware("http")
async def logging_middleware_handler(request: Request, call_next):
    """Logging middleware handler"""
    try:
        # Process request through logging middleware
        request_data = await logging_middleware.process_request(request)
        
        # Process request
        response = await call_next(request)
        
        # Process response through logging middleware
        await logging_middleware.process_response(request, response, request_data)
        
        return response
        
    except Exception as e:
        logger.error(f"Logging middleware error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Logging middleware failed", "code": "LOGGING_ERROR"}
        )

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return await error_handler_middleware.handle_exception(request, exc)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation exceptions"""
    return await error_handler_middleware.handle_exception(request, exc)

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    return await error_handler_middleware.handle_exception(request, exc)

# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Ekam NLP Query Engine API",
        "version": "1.0.0",
        "description": "Natural Language Query Engine for Employee Database",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "timestamp": time.time()
    }

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": time.time(),
        "services": {
            "api": "healthy",
            "database": "unknown",
            "redis": "unknown",
            "chromadb": "unknown"
        }
    }

# Include API routers
app.include_router(schema_endpoints.router)
app.include_router(document_endpoints.router)
app.include_router(query_endpoints.router)

# Main application entry point
if __name__ == "__main__":
    uvicorn.run(
        "api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
