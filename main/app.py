"""
DocuMagnetIR - Streamlit Application

A UI interface for the document extractor and sorter with extraction
and embedding pipelines for academic papers and syllabus.
"""

import streamlit as st
import time
from pathlib import Path
import sys


# Configure page settings
st.set_page_config(
    page_title="DocuMagnetIR",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(
    """
    <style>
    .ascii-art {
        font-family: "Lucida Console", Monaco, monospace; /* Or another monospaced font */
        font-size: 15px;
        line-height: 1.2;
        white-space: pre;
    }
    </style>
    <div class="ascii-art">
    ██╗███╗---██╗███████╗-██████╗-██████╗-███╗---███╗-█████╗-████████╗██╗-██████╗-███╗---██╗----██████╗-███████╗████████╗██████╗-██╗███████╗██╗---██╗-█████╗-██╗-----------
    ██║████╗--██║██╔════╝██╔═══██╗██╔══██╗████╗-████║██╔══██╗╚══██╔══╝██║██╔═══██╗████╗--██║----██╔══██╗██╔════╝╚══██╔══╝██╔══██╗██║██╔════╝██║---██║██╔══██╗██║-----------
    ██║██╔██╗-██║█████╗--██║---██║██████╔╝██╔████╔██║███████║---██║---██║██║---██║██╔██╗-██║----██████╔╝█████╗-----██║---██████╔╝██║█████╗--██║---██║███████║██║-----------
    ██║██║╚██╗██║██╔══╝--██║---██║██╔══██╗██║╚██╔╝██║██╔══██║---██║---██║██║---██║██║╚██╗██║----██╔══██╗██╔══╝-----██║---██╔══██╗██║██╔══╝--╚██╗-██╔╝██╔══██║██║-----------
    ██║██║-╚████║██║-----╚██████╔╝██║--██║██║-╚═╝-██║██║--██║---██║---██║╚██████╔╝██║-╚████║----██║--██║███████╗---██║---██║--██║██║███████╗-╚████╔╝-██║--██║███████╗------
    ╚═╝╚═╝--╚═══╝╚═╝------╚═════╝-╚═╝--╚═╝╚═╝-----╚═╝╚═╝--╚═╝---╚═╝---╚═╝-╚═════╝-╚═╝--╚═══╝----╚═╝--╚═╝╚══════╝---╚═╝---╚═╝--╚═╝╚═╝╚══════╝--╚═══╝--╚═╝--╚═╝╚══════╝------
    -----------------------------------------------------------------------------------------------------------------------------------------------------------------------
    -█████╗-███╗---██╗██████╗-----██╗----██╗███████╗██████╗------█████╗--██████╗-███████╗███╗---██╗████████╗███████╗-------------------------------------------------------
    ██╔══██╗████╗--██║██╔══██╗----██║----██║██╔════╝██╔══██╗----██╔══██╗██╔════╝-██╔════╝████╗--██║╚══██╔══╝██╔════╝-------------------------------------------------------
    ███████║██╔██╗-██║██║--██║----██║-█╗-██║█████╗--██████╔╝----███████║██║--███╗█████╗--██╔██╗-██║---██║---███████╗--------------------{Final Project}--------------------
    ██╔══██║██║╚██╗██║██║--██║----██║███╗██║██╔══╝--██╔══██╗----██╔══██║██║---██║██╔══╝--██║╚██╗██║---██║---╚════██║-----------------{Vignesh Rajesh Babu}-----------------
    ██║--██║██║-╚████║██████╔╝----╚███╔███╔╝███████╗██████╔╝----██║--██║╚██████╔╝███████╗██║-╚████║---██║---███████║----------------------{04/27/2025}---------------------
    ╚═╝--╚═╝╚═╝--╚═══╝╚═════╝------╚══╝╚══╝-╚══════╝╚═════╝-----╚═╝--╚═╝-╚═════╝-╚══════╝╚═╝--╚═══╝---╚═╝---╚══════╝-------------------------------------------------------
        </div>
    """,
    unsafe_allow_html=True,
)

# Add custom CSS
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
    }
    h1, h2, h3 {
        margin-top: 0.5rem;
        margin-bottom: 1rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #00682F;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #00FF41;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Import custom modules
from ui.file_upload import upload_question_papers, upload_syllabus, check_files_exist
from ui.processing import run_document_processing, run_syllabus_processing, check_processing_completed
from ui.visualization import (
    load_question_data, load_tagged_questions, 
    display_question_type_distribution, display_topics_subtopics, display_source_distribution
)
from ui.embedding import generate_embeddings, check_embeddings_exist
from ui.tagging import generate_tags, check_tags_exist
from ui.query_engine import create_query_interface, create_filtered_search
from ui.cleanup import create_cleanup_interface

# Main app header
st.title("DocuMagnetIR 🧲")
st.subheader("Document Extractor & Question Search Engine")

# Create tabs
tabs = st.tabs([
    "📄 Upload Files", 
    "⚙️ Process Data", 
    "📊 Visualization", 
    "🔍 Search",
    "🧹 Cleanup"
])

# Tab 1: File Upload
with tabs[0]:
    st.markdown("### Upload Files")
    st.markdown("""
    Start by uploading your PDF files:
    1. Upload one or more PDF question papers
    2. Upload a syllabus PDF
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Question papers upload
        question_papers = upload_question_papers()
    
    with col2:
        # Syllabus upload
        syllabus_file = upload_syllabus()
    
    # Check if files exist
    files_exist, message = check_files_exist()
    st.info(message)

# Tab 2: Process Data
with tabs[1]:
    st.markdown("### Process Documents and Syllabus")
    st.markdown("""
    Process the uploaded documents to extract questions and analyze the syllabus.
    This step will:
    1. Extract text from the PDFs
    2. Identify questions and their structure
    3. Analyze the syllabus to extract topics and subtopics
    4. Generate question embeddings for semantic search
    """)
    
    # Check if files exist before showing processing buttons
    files_exist, message = check_files_exist()
    if not files_exist:
        st.warning(message)
    else:
        col1, col2 = st.columns(2)
        
        # Process Documents Button
        with col1:
            st.subheader("Document Processing")
            if st.button("Process Question Documents", type="primary", key="process_docs_button"):
                with st.spinner("Processing documents..."):
                    result = run_document_processing()
                    
                    if result["success"]:
                        st.success(result["message"])
                    else:
                        st.error(result["message"])
        
        # Process Syllabus Button
        with col2:
            st.subheader("Syllabus Processing")
            if st.button("Process Syllabus", type="primary", key="process_syllabus_button"):
                with st.spinner("Processing syllabus..."):
                    result = run_syllabus_processing()
                    
                    if result["success"]:
                        st.success(result["message"])
                    else:
                        st.error(result["message"])
        
        # Horizontal Line
        st.markdown("---")
        
        # Check if processing is completed
        processing_completed = check_processing_completed()
        
        # Embedding Generation and Tagging section
        st.subheader("Embedding Generation and Tagging")
        if not processing_completed:
            st.warning("Please complete document and syllabus processing first.")
        else:
            # Force regenerate option and auto-tag control
            col1, col2 = st.columns([3, 1])
            with col1:
                force_regenerate = st.checkbox("Force regeneration of embeddings", value=False)
            with col2:
                disable_auto_tag = st.checkbox("Disable auto-tagging", value=False)
            
            if st.button("Generate Embeddings", type="primary", key="generate_embeddings_button"):
                with st.spinner("Generating embeddings and tagging questions..."):
                    result = generate_embeddings(force_regenerate=force_regenerate, auto_tag=not disable_auto_tag)
                    
                    if result["success"]:
                        st.success(result["message"])
                    else:
                        st.error(result["message"])
            
            # Manual tagging option (only show if embeddings exist)
            if check_embeddings_exist():
                st.subheader("Question Tagging (Manual)")
                if st.button("Tag Questions Manually", type="primary", key="tag_questions_button"):
                    with st.spinner("Tagging questions..."):
                        result = generate_tags()
                        
                        if result["success"]:
                            st.success(result["message"])
                        else:
                            st.error(result["message"])

# Tab 3: Visualization
with tabs[2]:
    st.markdown("### Data Visualization")
    
    # Check if processing is completed
    processing_completed = check_processing_completed()
    
    if not processing_completed:
        st.warning("Please complete document and syllabus processing first.")
    else:
        # Load question data
        questions = load_question_data()
        tagged_questions = load_tagged_questions()
        
        if questions:
            st.subheader("Question Statistics")
            
            # Split into columns
            col1, col2 = st.columns(2)
            
            # Question type distribution
            with col1:
                st.markdown("#### Question Type Distribution")
                display_question_type_distribution(questions)
            
            # Source distribution
            with col2:
                st.markdown("#### Source Distribution")
                display_source_distribution(questions)
            
            # Topic distribution (if tagged questions available)
            st.markdown("---")
            st.subheader("Topics and Subtopics")
            
            # Check if tagged questions exist, otherwise prompt the user
            if check_tags_exist():
                display_topics_subtopics(tagged_questions)
            else:
                st.warning("Tagged questions data not available.")
                
                # Only show the button if embeddings exist but tags don't
                if check_embeddings_exist():
                    if st.button("Generate Tags Now", type="primary"):
                        with st.spinner("Tagging questions..."):
                            result = generate_tags()
                            
                            if result["success"]:
                                st.success(result["message"])
                                # Clear the cache and rerun to show the new tags
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error(result["message"])
                else:
                    st.info("Complete document processing and generate embeddings first, then you can tag questions.")
        else:
            st.warning("No question data available. Please process documents first.")

# Tab 4: Search
with tabs[3]:
    st.markdown("### Question Search")
    
    if not check_embeddings_exist():
        st.warning("Embeddings not found. Please generate embeddings first.")
    else:
        # Create tabs for different search modes
        search_tabs = st.tabs(["Semantic Search", "Filtered Search"])
        
        with search_tabs[0]:
            create_query_interface()
            
        with search_tabs[1]:
            create_filtered_search()

# Tab 5: Cleanup
with tabs[4]:
    create_cleanup_interface()

# Footer
st.markdown("---")
st.markdown(
    "**DocuMagnetIR** 🧲 is a document extraction and question retrieval system designed for academic papers, with specialized support for mathematical notation. It extracts questions from academic PDFs, processes and tags them, and provides a powerful search interface. "
    "Final Project submission by Vignesh R Babu (Spring'25 MSE DS) for Information Retrieval and Web Agents (EN601.466)"
)