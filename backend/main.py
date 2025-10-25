"""
Main FastAPI application entry point for NLP Query Engine
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from config import setup_logging, settings
from api.services.database_initializer import initialize_database_services
from api.services.health_monitor import initialize_health_monitor
from api.services.schema_service import initialize_schema_service
from api.services.document_processor import initialize_document_processor
from api.services.query_classifier import initialize_query_classifier
from api.services.sql_generator import initialize_sql_generator
from api.services.document_search_engine import initialize_document_search_engine
from api.services.hybrid_query_processor import initialize_hybrid_query_processor
from api.endpoints import schema_endpoints, document_endpoints, query_endpoints, ingestion_endpoints

# Setup logging
logger = setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    try:
        logger.info("Initializing database services...")
        db_initializer = initialize_database_services()
        result = db_initializer.initialize_all_services()
        
        if result["status"] == "success":
            logger.info("Database services initialized successfully")
            
            # Initialize health monitoring
            logger.info("Initializing health monitoring...")
            health_monitor = initialize_health_monitor()
            logger.info("Health monitoring initialized successfully")
            
            # Initialize schema service
            logger.info("Initializing schema service...")
            try:
                schema_service = initialize_schema_service()
                logger.info("Schema service initialized successfully")
            except Exception as e:
                logger.warning(f"Schema service initialization failed: {str(e)}")
                logger.info("Schema service will be initialized on first use")
            
            # Initialize document processor
            logger.info("Initializing document processor...")
            try:
                document_processor = initialize_document_processor()
                logger.info("Document processor initialized successfully")
            except Exception as e:
                logger.warning(f"Document processor initialization failed: {str(e)}")
                logger.info("Document processor will be initialized on first use")
            
            # Initialize query services
            logger.info("Initializing query services...")
            try:
                query_classifier = initialize_query_classifier()
                logger.info("Query classifier initialized successfully")
            except Exception as e:
                logger.warning(f"Query classifier initialization failed: {str(e)}")
                logger.info("Query classifier will be initialized on first use")
            
            try:
                sql_generator = initialize_sql_generator()
                logger.info("SQL generator initialized successfully")
            except Exception as e:
                logger.warning(f"SQL generator initialization failed: {str(e)}")
                logger.info("SQL generator will be initialized on first use")
            
            try:
                document_search_engine = initialize_document_search_engine()
                logger.info("Document search engine initialized successfully")
            except Exception as e:
                logger.warning(f"Document search engine initialization failed: {str(e)}")
                logger.info("Document search engine will be initialized on first use")
            
            try:
                hybrid_query_processor = initialize_hybrid_query_processor()
                logger.info("Hybrid query processor initialized successfully")
            except Exception as e:
                logger.warning(f"Hybrid query processor initialization failed: {str(e)}")
                logger.info("Hybrid query processor will be initialized on first use")
        else:
            logger.error(f"Database services initialization failed: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Failed to initialize database services: {str(e)}")
    
    yield
    
    # Shutdown
    try:
        from api.services.database_initializer import get_database_initializer
        db_initializer = get_database_initializer()
        db_initializer.close_all_services()
        logger.info("Database services closed")
    except Exception as e:
        logger.error(f"Error closing database services: {str(e)}")

app = FastAPI(
    title="NLP Query Engine for Employee Data",
    description="Natural language query system for employee databases with dynamic schema discovery",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    logger.info("Root endpoint accessed")
    return {"message": "NLP Query Engine for Employee Data API"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.info("Health check endpoint accessed")
    return {
        "status": "healthy", 
        "service": "nlp-query-engine",
        "version": "1.0.0",
        "database_url": settings.DATABASE_URL,
        "redis_url": settings.REDIS_URL,
        "chroma_url": settings.CHROMA_URL
    }

@app.get("/database/status")
async def database_status():
    """Database services status endpoint"""
    try:
        from api.services.database_initializer import get_database_initializer
        db_initializer = get_database_initializer()
        status = db_initializer.get_service_status()
        return status
    except Exception as e:
        logger.error(f"Failed to get database status: {str(e)}")
        return {"status": "error", "error": str(e)}

@app.get("/health/comprehensive")
async def comprehensive_health():
    """Comprehensive health check endpoint"""
    try:
        from api.services.health_monitor import get_health_monitor
        health_monitor = get_health_monitor()
        health_status = health_monitor.get_comprehensive_health_status()
        return health_status
    except Exception as e:
        logger.error(f"Failed to get comprehensive health status: {str(e)}")
        return {"status": "error", "error": str(e)}

@app.get("/health/alerts")
async def health_alerts():
    """Health alerts endpoint"""
    try:
        from api.services.health_monitor import get_health_monitor
        health_monitor = get_health_monitor()
        alerts = health_monitor.check_alerts()
        return {"alerts": alerts, "count": len(alerts)}
    except Exception as e:
        logger.error(f"Failed to get health alerts: {str(e)}")
        return {"status": "error", "error": str(e)}

@app.get("/health/history")
async def health_history(hours: int = 24):
    """Health monitoring history endpoint"""
    try:
        from api.services.health_monitor import get_health_monitor
        health_monitor = get_health_monitor()
        history = health_monitor.get_health_history(hours)
        return {"history": history, "hours": hours}
    except Exception as e:
        logger.error(f"Failed to get health history: {str(e)}")
        return {"status": "error", "error": str(e)}

# Include API routers
app.include_router(ingestion_endpoints.router)
app.include_router(schema_endpoints.router)
app.include_router(document_endpoints.router)
app.include_router(query_endpoints.router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
