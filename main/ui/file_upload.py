"""
File upload module for DocuMagnetIR Streamlit application.
Handles file uploads for question papers and syllabus.
"""

import os
import streamlit as st
import shutil
from pathlib import Path

# Base paths
current_file = Path(__file__)
BASE_DIR = current_file.parent.parent.parent
SAMPLE_PAPERS_DIR = BASE_DIR / "data" / "sample_papers"
SYLLABUS_DIR = BASE_DIR / "data" / "syllabus"

def ensure_directories():
    """Ensure all necessary directories exist."""
    SAMPLE_PAPERS_DIR.mkdir(parents=True, exist_ok=True)
    SYLLABUS_DIR.mkdir(parents=True, exist_ok=True)

def upload_question_papers():
    """
    Handle upload of question paper PDFs.
    
    Returns:
        list: List of uploaded file paths
    """
    ensure_directories()
    
    st.subheader("Upload Question Papers")
    uploaded_files = st.file_uploader(
        "Upload PDF question papers", 
        type=["pdf"], 
        accept_multiple_files=True,
        help="Select one or more PDF files containing exam questions"
    )
    
    uploaded_paths = []
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            file_path = SAMPLE_PAPERS_DIR / uploaded_file.name
            
            # Check if file already exists
            if file_path.exists():
                overwrite = st.checkbox(f"File {uploaded_file.name} already exists. Overwrite?", key=f"overwrite_{uploaded_file.name}")
                if not overwrite:
                    st.info(f"Skipping {uploaded_file.name}")
                    continue
            
            # Save the file
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            st.success(f"Saved {uploaded_file.name}")
            uploaded_paths.append(str(file_path))
    
    return uploaded_paths

def upload_syllabus():
    """
    Handle upload of syllabus PDF.
    
    Returns:
        str: Path to the uploaded syllabus or None
    """
    ensure_directories()
    
    st.subheader("Upload Syllabus")
    uploaded_file = st.file_uploader(
        "Upload syllabus PDF", 
        type=["pdf"],
        help="Select a PDF file containing the course syllabus"
    )
    
    if uploaded_file:
        file_path = SYLLABUS_DIR / uploaded_file.name
        
        # Check if file already exists
        if file_path.exists():
            overwrite = st.checkbox(f"File {uploaded_file.name} already exists. Overwrite?", key="overwrite_syllabus")
            if not overwrite:
                st.info(f"Skipping {uploaded_file.name}")
                return None
        
        # Save the file
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.success(f"Saved {uploaded_file.name}")
        return str(file_path)
    
    return None

def check_files_exist():
    """
    Check if necessary files exist.
    
    Returns:
        tuple: (bool, str) indicating if files exist and a message
    """
    # Check for question papers
    question_papers = list(SAMPLE_PAPERS_DIR.glob("*.pdf"))
    if not question_papers:
        return False, "No question papers found. Please upload at least one question paper."
    
    # Check for syllabus
    syllabus_files = list(SYLLABUS_DIR.glob("*.pdf"))
    if not syllabus_files:
        return False, "No syllabus found. Please upload a syllabus."
    
    return True, f"Found {len(question_papers)} question paper(s) and {len(syllabus_files)} syllabus file(s)."