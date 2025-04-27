"""
Processing module for DocuMagnetIR Streamlit application.
Handles document and syllabus processing workflows.
"""

import os
import asyncio
import streamlit as st
from pathlib import Path
import sys
import json

# Add project root to path for imports
current_file = Path(__file__)
BASE_DIR = current_file.parent.parent.parent
sys.path.append(str(BASE_DIR))

# Import processing functions
# These will be imported when the module is used
from main.extraction.main_questions_extraction import process_documents
from main.extraction.main_syllabus_extraction import process_syllabus_documents


# Define paths
OCR_RESULTS_DIR = BASE_DIR / "data" / "ocr_results"
QUESTION_BANK_PATH = BASE_DIR / "results_question_bank" / "question_bank.json"
SYLLABUS_RESULTS_DIR = BASE_DIR / "data" / "syllabus_extract_ocr"

@st.cache_data
def run_document_processing():
    """
    Run the document processing pipeline.
    
    Returns:
        dict: Processing results with success status and message
    """
    try:
        # Create an asyncio event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run the document processing function
        result = loop.run_until_complete(process_documents())
        loop.close()
        
        # Check if question bank was generated
        if QUESTION_BANK_PATH.exists():
            with open(QUESTION_BANK_PATH, 'r') as f:
                question_bank = json.load(f)
            num_questions = len(question_bank)
            return {
                "success": True,
                "message": f"Document processing completed successfully. Extracted {num_questions} questions.",
                "num_questions": num_questions
            }
        else:
            return {
                "success": False,
                "message": "Document processing completed but no question bank was generated."
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error in document processing: {str(e)}"
        }

@st.cache_data
def run_syllabus_processing():
    """
    Run the syllabus processing pipeline.
    
    Returns:
        dict: Processing results with success status and message
    """
    try:
        # Create an asyncio event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run the syllabus processing function
        result = loop.run_until_complete(process_syllabus_documents())
        loop.close()
        
        # Check if syllabus was processed
        syllabus_folders = list(SYLLABUS_RESULTS_DIR.glob("*"))
        if syllabus_folders:
            return {
                "success": True,
                "message": f"Syllabus processing completed successfully. Found {len(syllabus_folders)} processed syllabus folders."
            }
        else:
            return {
                "success": False,
                "message": "Syllabus processing completed but no results were found."
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error in syllabus processing: {str(e)}"
        }

def get_question_data():
    """
    Get processed question data.
    
    Returns:
        dict or None: Question bank data if available
    """
    if QUESTION_BANK_PATH.exists():
        with open(QUESTION_BANK_PATH, 'r') as f:
            return json.load(f)
    return None

def get_syllabus_data():
    """
    Get processed syllabus data.
    
    Returns:
        dict or None: Syllabus data if available
    """
    analyzed_files = list(SYLLABUS_RESULTS_DIR.glob("*/*_analyzed.json"))
    if analyzed_files:
        with open(analyzed_files[0], 'r') as f:
            return json.load(f)
    return None

def check_processing_completed():
    """
    Check if both document and syllabus processing have been completed.
    
    Returns:
        bool: True if both have been completed, False otherwise
    """
    question_data = get_question_data()
    syllabus_data = get_syllabus_data()
    
    return question_data is not None and syllabus_data is not None