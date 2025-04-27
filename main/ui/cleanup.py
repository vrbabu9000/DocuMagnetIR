"""
Cleanup module for DocuMagnetIR Streamlit application.
Handles cleaning up processed data and files.
"""

import os
import streamlit as st
import shutil
from pathlib import Path

# Define base directory and paths to clean
BASE_DIR = Path("D:/MSE_DS_JHU/Semester1/Information_Retrieval_Web_Agents/Git/DocuMagnetIR")

PATHS_TO_CLEAN = [
    BASE_DIR / "data" / "ocr_results",
    BASE_DIR / "data" / "syllabus_extract_ocr" / "cs466_Syllabus",
    BASE_DIR / "data" / "sample_papers",
    BASE_DIR / "data" / "syllabus",
    BASE_DIR / "main" / "embeddings" / "question_embeddings.pkl",
    BASE_DIR / "main" / "embeddings" / "question_metadata.json",
    BASE_DIR / "results_question_bank"
]

def clean_directory(directory_path):
    """
    Remove all files and subdirectories from the specified directory.
    
    Args:
        directory_path (Path): Directory to clean
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not directory_path.exists():
            return True
            
        if directory_path.is_file():
            directory_path.unlink()
        else:
            # Remove all contents of the directory
            shutil.rmtree(directory_path)
            # Recreate the directory
            directory_path.mkdir(parents=True, exist_ok=True)
            
        return True
    except Exception as e:
        st.error(f"Error cleaning {directory_path}: {str(e)}")
        return False

def clean_file(file_path):
    """
    Remove a specific file.
    
    Args:
        file_path (Path): File to remove
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if file_path.exists():
            file_path.unlink()
        return True
    except Exception as e:
        st.error(f"Error removing {file_path}: {str(e)}")
        return False

def clean_all_data():
    """
    Clean all processed data.
    
    Returns:
        dict: Results with success status and message
    """
    success_count = 0
    failure_count = 0
    
    for path in PATHS_TO_CLEAN:
        if path.exists():
            if path.is_file():
                if clean_file(path):
                    success_count += 1
                else:
                    failure_count += 1
            else:
                if clean_directory(path):
                    success_count += 1
                else:
                    failure_count += 1
    
    if failure_count == 0:
        return {
            "success": True,
            "message": f"Successfully cleaned {success_count} paths."
        }
    else:
        return {
            "success": False,
            "message": f"Cleaned {success_count} paths, but failed to clean {failure_count} paths."
        }

def create_cleanup_interface():
    """
    Create the cleanup interface.
    """
    st.header("Data Cleanup")
    
    st.warning(
        "This will remove all processed data including:\n"
        "- Extracted question papers\n"
        "- Processed syllabus\n"
        "- Generated embeddings\n"
        "- Tagged questions\n\n"
        "Make sure you have backed up any important data before proceeding."
    )
    
    confirm = st.checkbox("I understand and want to proceed with cleanup")
    
    if confirm:
        if st.button("Clean All Data", type="primary", key="clean_data_button"):
            with st.spinner("Cleaning data..."):
                result = clean_all_data()
                
                if result["success"]:
                    st.success(result["message"])
                    # Clear all cache to ensure clean state
                    st.cache_data.clear()
                    st.cache_resource.clear()
                    st.rerun()
                else:
                    st.error(result["message"])