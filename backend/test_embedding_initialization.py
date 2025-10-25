#!/usr/bin/env python3
"""
Test script for embedding model initialization
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

def test_embedding_initialization():
    """Test embedding model initialization"""
    try:
        logger.info("Testing embedding model initialization...")
        
        # Test lazy initialization
        logger.info("Testing lazy initialization of document processor...")
        document_processor = get_or_initialize_document_processor()
        
        # Check if embedding model is initialized
        if document_processor.embedding_model:
            logger.info("Embedding model is initialized successfully!")
            logger.info(f"Model type: {type(document_processor.embedding_model)}")
            
            # Test embedding generation
            logger.info("Testing embedding generation...")
            test_text = "This is a test document for embedding generation."
            embeddings = document_processor._generate_embeddings([{"text": test_text}])
            
            if embeddings and len(embeddings) > 0:
                logger.info(f"Embedding generation successful! Generated {len(embeddings)} embeddings")
                logger.info(f"Embedding dimension: {len(embeddings[0])}")
            else:
                logger.error("Embedding generation failed")
                return False
                
        else:
            logger.error("Embedding model is not initialized")
            return False
        
        # Test document processing with a simple text file
        logger.info("Testing document processing...")
        test_file = "test_embedding.txt"
        test_content = """
        Test Document for Embedding
        
        This is a test document to verify that the embedding model
        is working correctly with the document processor.
        
        Skills: Python, JavaScript, SQL
        Experience: 5 years software development
        Education: Computer Science Degree
        """
        
        # Create test file
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        logger.info(f"Created test file: {test_file}")
        
        # Process the document
        result = document_processor.process_single_document(test_file)
        
        if result["success"]:
            logger.info("Document processing successful!")
            logger.info(f"Document ID: {result['document_id']}")
            logger.info(f"Document Type: {result['doc_type']}")
            logger.info(f"Chunks Count: {result['chunks_count']}")
        else:
            logger.error(f"Document processing failed: {result.get('error', 'Unknown error')}")
            return False
        
        # Clean up
        if os.path.exists(test_file):
            os.remove(test_file)
            logger.info("Cleaned up test file")
        
        logger.info("Embedding initialization test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        return False

def test_embedding_model_loading():
    """Test different embedding models"""
    try:
        logger.info("Testing different embedding models...")
        
        from sentence_transformers import SentenceTransformer
        
        models_to_test = [
            'all-MiniLM-L6-v2',
            'paraphrase-MiniLM-L6-v2',
            'all-mpnet-base-v2'
        ]
        
        for model_name in models_to_test:
            try:
                logger.info(f"Testing model: {model_name}")
                model = SentenceTransformer(model_name)
                
                # Test encoding
                test_texts = ["This is a test", "Another test document"]
                embeddings = model.encode(test_texts)
                
                logger.info(f"Model {model_name} loaded successfully!")
                logger.info(f"Generated {len(embeddings)} embeddings with dimension {len(embeddings[0])}")
                
            except Exception as e:
                logger.warning(f"Model {model_name} failed: {str(e)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Model testing failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Embedding Model Initialization Test")
    print("=" * 60)
    
    # Test embedding initialization
    success1 = test_embedding_initialization()
    
    print("\n" + "=" * 60)
    print("Embedding Model Loading Test")
    print("=" * 60)
    
    # Test different models
    success2 = test_embedding_model_loading()
    
    overall_success = success1 and success2
    print(f"\nOverall test result: {'PASSED' if overall_success else 'FAILED'}")
    sys.exit(0 if overall_success else 1)
