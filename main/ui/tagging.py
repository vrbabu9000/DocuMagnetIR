"""
Tagging module for DocuMagnetIR Streamlit application.
Handles question tagging functionality.
"""

import os
import streamlit as st
import sys
from pathlib import Path
import json

# Add project root to path for imports
current_file = Path(__file__)
BASE_DIR = current_file.parent.parent.parent
sys.path.append(str(BASE_DIR))

# Import question tagger
from main.embeddings.question_tagger import QuestionTopicTagger

# Define paths
EMBEDDINGS_DIR = BASE_DIR / "main" / "embeddings"
EMBEDDING_PATH = EMBEDDINGS_DIR / "question_embeddings.pkl"
METADATA_PATH = EMBEDDINGS_DIR / "question_metadata.json"
SYLLABUS_DIR = BASE_DIR / "data" / "syllabus_extract_ocr"
TAGGED_QUESTIONS_PATH = BASE_DIR / "results_question_bank" / "tagged_questions.json"

@st.cache_resource
def get_question_tagger():
    """
    Create and return a QuestionTopicTagger instance.
    
    Returns:
        QuestionTopicTagger or None: An instance of the tagger if paths exist, None otherwise
    """
    # Check if required files exist
    if not EMBEDDING_PATH.exists() or not METADATA_PATH.exists():
        return None
    
    # Find the syllabus file
    syllabus_files = list(SYLLABUS_DIR.glob("*/*_analyzed.json"))
    if not syllabus_files:
        return None
    
    # Create output directory if it doesn't exist
    TAGGED_QUESTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize the tagger
    tagger = QuestionTopicTagger(
        question_embedding_path=str(EMBEDDING_PATH),
        question_metadata_path=str(METADATA_PATH),
        syllabus_path=str(syllabus_files[0]),
        output_path=str(TAGGED_QUESTIONS_PATH)
    )
    
    return tagger

def generate_tags():
    """
    Generate tags for questions.
    
    Returns:
        dict: Results with success status and message
    """
    if not EMBEDDING_PATH.exists() or not METADATA_PATH.exists():
        return {
            "success": False,
            "message": "Embeddings not found. Please generate embeddings first."
        }
    
    # Find analyzed syllabus files
    syllabus_files = list(SYLLABUS_DIR.glob("*/*_analyzed.json"))
    if not syllabus_files:
        return {
            "success": False,
            "message": "Processed syllabus not found. Please process syllabus first."
        }
    
    try:
        # Get the question tagger
        tagger = get_question_tagger()
        if tagger is None:
            return {
                "success": False,
                "message": "Failed to initialize question tagger."
            }
        
        # Run the tagging process
        organized_data = tagger.run()
        
        # Calculate statistics
        topic_count = len(organized_data["topics"])
        question_count = sum(
            len(question_list["questions"]) 
            for topic in organized_data["topics"] 
            for question_list in topic["subtopics"]
        )
        
        return {
            "success": True,
            "message": f"Successfully tagged {question_count} questions across {topic_count} topics.",
            "topic_count": topic_count,
            "question_count": question_count
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error generating tags: {str(e)}"
        }

def check_tags_exist():
    """
    Check if tags have been generated.
    
    Returns:
        bool: True if tags exist, False otherwise
    """
    return TAGGED_QUESTIONS_PATH.exists()

def load_tagged_questions():
    """
    Load the tagged questions data.
    
    Returns:
        dict or None: Tagged questions data if file exists, None otherwise
    """
    if TAGGED_QUESTIONS_PATH.exists():
        with open(TAGGED_QUESTIONS_PATH, 'r') as f:
            return json.load(f)
    return None