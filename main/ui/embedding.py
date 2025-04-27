"""
Embedding module for DocuMagnetIR Streamlit application.
Handles generation and management of question embeddings.
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

# Import embedding generator
from main.embeddings.question_embedding_generator import QuestionEmbeddingGenerator

# Define paths
QUESTION_BANK_PATH = BASE_DIR / "results_question_bank" / "question_bank.json"
EMBEDDINGS_DIR = BASE_DIR / "main" / "embeddings"
EMBEDDING_PATH = EMBEDDINGS_DIR / "question_embeddings.pkl"
METADATA_PATH = EMBEDDINGS_DIR / "question_metadata.json"

@st.cache_resource
def get_embedding_generator():
    """
    Create and return a QuestionEmbeddingGenerator instance.
    
    Returns:
        QuestionEmbeddingGenerator: An instance of the embedding generator
    """
    # Create output directory if it doesn't exist
    EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Initialize the generator
    generator = QuestionEmbeddingGenerator(
        model_name="all-MiniLM-L6-v2",
        embedding_path=str(EMBEDDING_PATH),
        metadata_path=str(METADATA_PATH)
    )
    
    return generator

def generate_embeddings(force_regenerate=False, auto_tag=True):
    """
    Generate embeddings for the question bank.
    
    Args:
        force_regenerate (bool): Whether to force regeneration of embeddings
        auto_tag (bool): Whether to automatically tag questions after generating embeddings
        
    Returns:
        dict: Results with success status and message
    """
    if not QUESTION_BANK_PATH.exists():
        return {
            "success": False,
            "message": "Question bank not found. Please process documents first."
        }
    
    try:
        # Get the embedding generator
        generator = get_embedding_generator()
        
        # Generate embeddings
        embeddings, metadata = generator.process_question_bank(
            str(QUESTION_BANK_PATH), 
            force_regenerate=force_regenerate
        )
        
        result = {
            "success": True,
            "message": f"Successfully generated embeddings for {len(metadata)} questions.",
            "num_questions": len(metadata),
            "embedding_dim": embeddings.shape[1]
        }
        
        # Auto-tag if requested
        if auto_tag:
            # Import here to avoid circular imports
            from main.ui.tagging import generate_tags
            
            tag_result = generate_tags()
            
            if tag_result["success"]:
                result["message"] += f" {tag_result['message']}"
            else:
                result["message"] += f" However, automatic tagging failed: {tag_result['message']}"
        
        return result
    except Exception as e:
        return {
            "success": False,
            "message": f"Error generating embeddings: {str(e)}"
        }

def search_similar_questions(query, top_k=5):
    """
    Search for questions similar to the query.
    
    Args:
        query (str): Query text
        top_k (int): Number of results to return
        
    Returns:
        list or None: Search results if successful, None otherwise
    """
    if not EMBEDDING_PATH.exists() or not METADATA_PATH.exists():
        return None
    
    try:
        # Get the embedding generator
        generator = get_embedding_generator()
        
        # Load embeddings if not already loaded
        if generator.embeddings is None or generator.metadata is None:
            generator.load()
        
        # Search for similar questions
        results = generator.search_similar_questions(query, top_k=top_k)
        
        return results
    except Exception as e:
        st.error(f"Error searching for similar questions: {str(e)}")
        return None

def check_embeddings_exist():
    """
    Check if embeddings have been generated.
    
    Returns:
        bool: True if embeddings exist, False otherwise
    """
    return EMBEDDING_PATH.exists() and METADATA_PATH.exists()