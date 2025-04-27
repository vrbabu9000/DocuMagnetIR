"""
Query engine module for DocuMagnetIR Streamlit application.
Handles question search functionality.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import json

# Add project root to path for imports
current_file = Path(__file__)
BASE_DIR = current_file.parent.parent.parent
sys.path.append(str(BASE_DIR))

# Import from embedding module
from main.ui.embedding import search_similar_questions, check_embeddings_exist

def create_query_interface():
    """
    Create the query interface for searching questions.
    """
    st.header("Question Search")
    
    # Check if embeddings exist
    if not check_embeddings_exist():
        st.warning("Embeddings not found. Please generate embeddings first.")
        return
    
    # Query input
    query = st.text_input("Enter your search query:", placeholder="e.g., vector space model")
    
    # Number of results to show
    col1, col2 = st.columns([3, 1])
    with col2:
        top_k = st.slider("Number of results:", min_value=1, max_value=20, value=5)
    
    search_button = st.button("Search", key="search_button", type="primary")
    
    if search_button and query:
        # Show loading spinner
        with st.spinner("Searching..."):
            # Search for similar questions
            results = search_similar_questions(query, top_k=top_k)
            
            if results:
                display_search_results(query, results)
            else:
                st.error("No results found or an error occurred during search.")

def display_search_results(query, results):
    """
    Display search results in a nicely formatted way.
    
    Args:
        query (str): Query text
        results (list): Search results
    """
    st.subheader(f"Search Results for: '{query}'")
    
    for i, result in enumerate(results, 1):
        similarity_score = result.get('similarity_score', 0)
        question_number = result.get('question_number', 'Unknown')
        question_type = result.get('question_type', 'Unknown')
        source_file = result.get('source_file', 'Unknown')
        
        # Get the question text
        original_object = result.get('original_object', {})
        question_text = original_object.get('question_text', 'No text available')
        
        # Get topic information if available
        tags = result.get('tags', [])
        main_topic = tags[0].get('main_topic', 'Unknown') if tags else 'Unknown'
        subtopic = tags[0].get('subtopic', 'Unknown') if tags else 'Unknown'
        
        # Show the result
        with st.expander(f"#{i}: Question {question_number} (Score: {similarity_score:.4f})"):
            # Display metadata
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**Type:** {question_type}")
            with col2:
                st.markdown(f"**Source:** {source_file}")
            with col3:
                st.markdown(f"**Similarity:** {similarity_score:.4f}")
            
            # Display topic information
            if tags:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Main Topic:** {main_topic}")
                with col2:
                    st.markdown(f"**Subtopic:** {subtopic}")
            
            # Display question text
            st.markdown("---")
            st.markdown("**Question Text:**")
            st.markdown(question_text)

def create_filtered_search():
    """
    Create an interface for filtered search based on metadata.
    """
    st.header("Filtered Search")
    
    # Check if embeddings exist
    if not check_embeddings_exist():
        st.warning("Embeddings not found. Please generate embeddings first.")
        return
    
    from main.ui.embedding import get_embedding_generator
    
    # Get the embedding generator
    generator = get_embedding_generator()
    
    # Load metadata if not already loaded
    if generator.metadata is None:
        try:
            generator.load()
        except Exception as e:
            st.error(f"Error loading metadata: {str(e)}")
            return
    
    # Extract metadata for filtering
    question_types = set()
    source_files = set()
    
    for item in generator.metadata:
        if 'question_type' in item:
            question_types.add(item['question_type'])
        if 'source_file' in item:
            source_files.add(item['source_file'])
    
    # Convert to sorted lists
    question_types = sorted(list(question_types))
    source_files = sorted(list(source_files))
    
    # Create filters
    col1, col2 = st.columns(2)
    with col1:
        selected_type = st.selectbox("Filter by Question Type:", ["Any"] + question_types)
    with col2:
        selected_source = st.selectbox("Filter by Source File:", ["Any"] + source_files)
    
    # Query input
    query = st.text_input("Enter your search query (optional):", key="filtered_query")
    
    # Number of results to show
    col1, col2 = st.columns([3, 1])
    with col2:
        top_k = st.slider("Number of results:", min_value=1, max_value=20, value=10, key="filtered_top_k")
    
    search_button = st.button("Search", key="filtered_search_button")
    
    if search_button:
        # Filter the metadata based on selection
        filtered_results = []
        
        for item in generator.metadata:
            # Apply type filter
            if selected_type != "Any" and item.get('question_type') != selected_type:
                continue
                
            # Apply source filter
            if selected_source != "Any" and item.get('source_file') != selected_source:
                continue
            
            # Add to filtered results
            filtered_results.append(item)
        
        # Apply text search if query is provided
        if query:
            with st.spinner("Searching..."):
                # Search within filtered results
                search_results = search_similar_questions(query, top_k=top_k)
                
                if search_results:
                    # Filter search results by the metadata filters
                    final_results = []
                    for result in search_results:
                        # Apply type filter
                        if selected_type != "Any" and result.get('question_type') != selected_type:
                            continue
                            
                        # Apply source filter
                        if selected_source != "Any" and result.get('source_file') != selected_source:
                            continue
                        
                        final_results.append(result)
                    
                    display_search_results(query, final_results)
                else:
                    st.error("No results found matching your criteria.")
        else:
            # Just show filtered results by metadata
            display_filtered_results(filtered_results[:top_k])

def display_filtered_results(results):
    """
    Display filtered results based on metadata.
    
    Args:
        results (list): Filtered metadata results
    """
    if not results:
        st.warning("No questions match the selected filters.")
        return
    
    st.subheader(f"Found {len(results)} matching questions")
    
    for i, result in enumerate(results, 1):
        question_number = result.get('question_number', 'Unknown')
        question_type = result.get('question_type', 'Unknown')
        source_file = result.get('source_file', 'Unknown')
        
        # Get the question text
        original_object = result.get('original_object', {})
        question_text = original_object.get('question_text', 'No text available')
        
        # Show the result
        with st.expander(f"#{i}: Question {question_number} ({question_type})"):
            # Display metadata
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Type:** {question_type}")
            with col2:
                st.markdown(f"**Source:** {source_file}")
            
            # Display question text
            st.markdown("---")
            st.markdown("**Question Text:**")
            st.markdown(question_text)