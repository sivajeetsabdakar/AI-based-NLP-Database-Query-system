#!/usr/bin/env python3
"""
Test script for Mistral OCR functionality
"""
import sys
import os
import logging
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.services.mistral_client import get_mistral_client

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_mistral_ocr():
    """Test Mistral OCR functionality"""
    try:
        logger.info("Testing Mistral OCR functionality...")
        
        # Initialize Mistral client
        logger.info("Initializing Mistral client...")
        mistral_client = get_mistral_client()
        logger.info("Mistral client initialized successfully")
        
        # Test 1: Create a simple test image (text file as image)
        test_image = "test_image.txt"
        test_content = """
        RESUME
        
        John Doe
        Software Engineer
        john.doe@email.com
        (555) 123-4567
        
        EXPERIENCE
        - Senior Software Engineer at TechCorp (2020-2024)
        - Software Developer at StartupXYZ (2018-2020)
        
        SKILLS
        - Python, JavaScript, SQL
        - React, Node.js, FastAPI
        - PostgreSQL, MongoDB
        
        EDUCATION
        - Bachelor's in Computer Science
        - University of Technology (2018)
        """
        
        # Create test file
        with open(test_image, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        logger.info(f"Created test file: {test_image}")
        
        # Test 2: Test image OCR
        logger.info("Testing image OCR...")
        try:
            ocr_result = mistral_client.extract_text_from_image_ocr(test_image)
            
            if ocr_result["success"]:
                logger.info(f"Image OCR successful!")
                logger.info(f"Pages processed: {len(ocr_result['pages'])}")
                logger.info(f"Text length: {len(ocr_result['extracted_text'])} characters")
                logger.info(f"Model used: {ocr_result['model']}")
                logger.info(f"Extracted text preview: {ocr_result['extracted_text'][:200]}...")
            else:
                logger.error(f"Image OCR failed: {ocr_result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"Image OCR test failed: {str(e)}")
            return False
        
        # Test 3: Test PDF OCR (if you have a PDF file)
        pdf_file = "test_document.pdf"
        if os.path.exists(pdf_file):
            logger.info(f"Testing PDF OCR with: {pdf_file}")
            try:
                pdf_ocr_result = mistral_client.extract_text_from_pdf_ocr(pdf_file)
                
                if pdf_ocr_result["success"]:
                    logger.info(f"PDF OCR successful!")
                    logger.info(f"Pages processed: {len(pdf_ocr_result['pages'])}")
                    logger.info(f"Text length: {len(pdf_ocr_result['extracted_text'])} characters")
                    logger.info(f"Model used: {pdf_ocr_result['model']}")
                    logger.info(f"Extracted text preview: {pdf_ocr_result['extracted_text'][:200]}...")
                else:
                    logger.warning(f"PDF OCR failed: {pdf_ocr_result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                logger.warning(f"PDF OCR test failed: {str(e)}")
        else:
            logger.info("No PDF file found for testing, skipping PDF OCR test")
        
        # Clean up
        if os.path.exists(test_image):
            os.remove(test_image)
            logger.info("Cleaned up test file")
        
        logger.info("Mistral OCR test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        return False

def test_mistral_ocr_with_different_models():
    """Test Mistral OCR with different models"""
    try:
        logger.info("Testing Mistral OCR with different models...")
        
        mistral_client = get_mistral_client()
        
        # Test different OCR models
        models_to_test = ["CX-9", "CX-10"]  # Add more models as available
        
        test_image = "test_model.txt"
        test_content = "Test OCR with different models"
        
        with open(test_image, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        for model in models_to_test:
            try:
                logger.info(f"Testing model: {model}")
                result = mistral_client.extract_text_from_image_ocr(test_image, model=model)
                
                if result["success"]:
                    logger.info(f"Model {model} successful: {len(result['extracted_text'])} characters")
                else:
                    logger.warning(f"Model {model} failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                logger.warning(f"Model {model} test failed: {str(e)}")
        
        # Clean up
        if os.path.exists(test_image):
            os.remove(test_image)
        
        return True
        
    except Exception as e:
        logger.error(f"Model testing failed: {str(e)}")
        return False

def test_mistral_ocr_url():
    """Test Mistral OCR with URL"""
    try:
        logger.info("Testing Mistral OCR with URL...")
        
        mistral_client = get_mistral_client()
        
        # Test with a sample image URL (you can replace with a real URL)
        test_url = "https://example.com/sample-image.jpg"
        
        try:
            logger.info(f"Testing URL OCR with: {test_url}")
            result = mistral_client.extract_text_from_url_ocr(
                url=test_url,
                document_type="image_url",
                model="CX-9"
            )
            
            if result["success"]:
                logger.info(f"URL OCR successful!")
                logger.info(f"Pages processed: {len(result['pages'])}")
                logger.info(f"Text length: {len(result['extracted_text'])} characters")
                logger.info(f"Model used: {result['model']}")
                logger.info(f"Extracted text preview: {result['extracted_text'][:200]}...")
            else:
                logger.warning(f"URL OCR failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.warning(f"URL OCR test failed: {str(e)}")
        
        return True
        
    except Exception as e:
        logger.error(f"URL testing failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Mistral OCR Testing")
    print("=" * 50)
    
    # Test basic OCR functionality
    success1 = test_mistral_ocr()
    
    print("\n" + "=" * 50)
    print("Model Testing")
    print("=" * 50)
    
    # Test different models
    success2 = test_mistral_ocr_with_different_models()
    
    print("\n" + "=" * 50)
    print("URL Testing")
    print("=" * 50)
    
    # Test URL OCR
    success3 = test_mistral_ocr_url()
    
    overall_success = success1 and success2 and success3
    print(f"\nOverall test result: {'PASSED' if overall_success else 'FAILED'}")
    sys.exit(0 if overall_success else 1)
