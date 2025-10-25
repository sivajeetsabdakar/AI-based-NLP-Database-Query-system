#!/usr/bin/env python3
"""
Test script for document processing fixes
"""
import sys
import os
import logging
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.services.document_processor import get_or_initialize_document_processor

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_document_processing_fixes():
    """Test document processing with fixes"""
    try:
        logger.info("Testing document processing fixes...")
        
        # Initialize document processor
        logger.info("Initializing document processor...")
        document_processor = get_or_initialize_document_processor()
        logger.info("Document processor initialized successfully")
        
        # Test with a simple text file
        test_file = "test_fixes.txt"
        test_content = """
        Test Document for Processing Fixes
        
        This is a test document to verify that the document processing
        fixes are working correctly.
        
        Skills: Python, JavaScript, SQL
        Experience: 5 years software development
        Education: Computer Science Degree
        
        Additional Information:
        - Project management experience
        - Team leadership skills
        - Database design expertise
        """
        
        # Create test file
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        logger.info(f"Created test file: {test_file}")
        
        # Process the document
        logger.info("Processing test document...")
        result = document_processor.process_single_document(test_file)
        
        if result["success"]:
            logger.info("Document processing successful!")
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
            logger.error(f"Document processing failed: {result.get('error', 'Unknown error')}")
            return False
        
        # Clean up
        if os.path.exists(test_file):
            os.remove(test_file)
            logger.info("Cleaned up test file")
        
        logger.info("Document processing fixes test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Document Processing Fixes Test")
    print("=" * 60)
    
    success = test_document_processing_fixes()
    
    print(f"\nTest result: {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)
