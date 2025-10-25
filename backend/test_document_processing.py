#!/usr/bin/env python3
"""
Test script for document processing functionality
"""
import sys
import os
import logging
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.services.document_processor import initialize_document_processor
from api.services.database_initializer import initialize_database_services

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_document_processing():
    """Test document processing functionality"""
    try:
        logger.info("Testing document processing...")
        
        # Initialize database services
        logger.info("Initializing database services...")
        db_initializer = initialize_database_services()
        result = db_initializer.initialize_all_services()
        
        if result["status"] != "success":
            logger.error(f"Database initialization failed: {result.get('error')}")
            return False
        
        logger.info("Database services initialized successfully")
        
        # Initialize document processor
        logger.info("Initializing document processor...")
        document_processor = initialize_document_processor()
        logger.info("Document processor initialized successfully")
        
        # Test with a simple text file
        test_file = "test_document.txt"
        test_content = """
        John Doe
        Software Engineer
        
        Experience:
        - 5 years of Python development
        - 3 years of React development
        - 2 years of database design
        
        Skills:
        - Python, JavaScript, SQL
        - React, Node.js, FastAPI
        - PostgreSQL, MongoDB
        
        Education:
        - Bachelor's in Computer Science
        - University of Technology
        """
        
        # Create test file
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        logger.info(f"Created test file: {test_file}")
        
        # Test Mistral OCR if available
        if document_processor.mistral_client:
            logger.info("Testing Mistral OCR integration...")
            try:
                # Test OCR with a simple text file (will be treated as image)
                ocr_result = document_processor.mistral_client.extract_text_from_image_ocr(test_file)
                if ocr_result["success"]:
                    logger.info(f"Mistral OCR test successful: {len(ocr_result['text'])} characters extracted")
                else:
                    logger.warning(f"Mistral OCR test failed: {ocr_result.get('error', 'Unknown error')}")
            except Exception as e:
                logger.warning(f"Mistral OCR test failed: {str(e)}")
        
        # Process the document
        logger.info("Processing test document...")
        result = document_processor.process_single_document(test_file)
        
        if result["success"]:
            logger.info(f"Document processed successfully!")
            logger.info(f"Document ID: {result['document_id']}")
            logger.info(f"Document Type: {result['doc_type']}")
            logger.info(f"Chunks Count: {result['chunks_count']}")
            
            # Test document search
            logger.info("Testing document search...")
            search_results = document_processor.search_documents("Python development", limit=5)
            logger.info(f"Found {len(search_results)} search results")
            
            for i, result in enumerate(search_results[:3]):
                logger.info(f"Result {i+1}: {result['metadata'].get('chunk_type', 'unknown')} - {result['text'][:100]}...")
            
        else:
            logger.error(f"Document processing failed: {result['error']}")
            return False
        
        # Clean up
        if os.path.exists(test_file):
            os.remove(test_file)
            logger.info("Cleaned up test file")
        
        logger.info("Document processing test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_document_processing()
    sys.exit(0 if success else 1)
