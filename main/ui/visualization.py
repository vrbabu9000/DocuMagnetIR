"""
Visualization module for DocuMagnetIR Streamlit application.
Handles displaying statistics and charts for processed questions.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import json
from pathlib import Path

# Define paths
current_file = Path(__file__)
BASE_DIR = current_file.parent.parent.parent
QUESTION_BANK_PATH = BASE_DIR / "results_question_bank" / "question_bank.json"
TAGGED_QUESTIONS_PATH = BASE_DIR / "results_question_bank" / "tagged_questions.json"

@st.cache_data
def load_question_data():
    """
    Load the question bank data.
    
    Returns:
        list or None: List of questions if file exists, None otherwise
    """
    if QUESTION_BANK_PATH.exists():
        with open(QUESTION_BANK_PATH, 'r') as f:
            return json.load(f)
    return None

@st.cache_data
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

def display_question_type_distribution(questions):
    """
    Display a pie chart of question types.
    
    Args:
        questions (list): List of question objects
    """
    if not questions:
        st.warning("No question data available")
        return
    
    # Count question types
    question_types = [q.get('question_type', 'Unknown') for q in questions]
    type_counts = Counter(question_types)
    
    # Create a DataFrame for the plot
    df = pd.DataFrame({
        'Question Type': list(type_counts.keys()),
        'Count': list(type_counts.values())
    })
    
    # Create a pie chart
    fig = px.pie(
        df, 
        names='Question Type', 
        values='Count',
        title='Question Type Distribution',
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    # Update layout for better appearance
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(
        autosize=True,
        margin=dict(l=20, r=20, t=30, b=20),
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display counts in a table as well
    st.markdown("### Question Counts by Type")
    st.dataframe(df.set_index('Question Type').sort_values('Count', ascending=False))

def display_topics_subtopics(tagged_data=None):
    """
    Display topics and subtopics from the tagged questions.
    
    Args:
        tagged_data (dict): Tagged questions data
    """
    # If no data provided, try to load it
    if tagged_data is None:
        tagged_data = load_tagged_questions()
        
    if not tagged_data or 'topics' not in tagged_data:
        st.warning("No tagged question data available. Generate embeddings with auto-tagging first.")
        return
    
    st.markdown(f"### Course: {tagged_data.get('course_name', 'Unknown')}")
    
    # Create a dictionary to store topic counts
    topic_counts = {}
    subtopic_details = {}
    
    for topic in tagged_data['topics']:
        topic_name = topic['name']
        subtopics = topic['subtopics']
        
        # Count questions in this topic
        total_questions = sum(len(subtopic['questions']) for subtopic in subtopics)
        topic_counts[topic_name] = total_questions
        
        # Store subtopic details
        subtopic_details[topic_name] = {}
        for subtopic in subtopics:
            subtopic_name = subtopic['name']
            subtopic_details[topic_name][subtopic_name] = len(subtopic['questions'])
    
    # Create a DataFrame for topic counts
    topics_df = pd.DataFrame({
        'Topic': list(topic_counts.keys()),
        'Question Count': list(topic_counts.values())
    }).sort_values('Question Count', ascending=False)
    
    # Display topic counts in a bar chart
    fig = px.bar(
        topics_df, 
        x='Topic', 
        y='Question Count',
        title='Questions by Topic',
        color='Topic',
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    fig.update_layout(
        xaxis_title="Topic",
        yaxis_title="Number of Questions",
        autosize=True,
        margin=dict(l=20, r=20, t=40, b=20),
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display topic details as an expandable tree
    st.markdown("### Detailed Topic Structure")
    
    for topic_name, count in topic_counts.items():
        with st.expander(f"{topic_name} ({count} questions)"):
            subtopics = subtopic_details[topic_name]
            subtopics_df = pd.DataFrame({
                'Subtopic': list(subtopics.keys()),
                'Question Count': list(subtopics.values())
            }).sort_values('Question Count', ascending=False)
            
            st.dataframe(subtopics_df)

def display_source_distribution(questions):
    """
    Display a bar chart of question sources.
    
    Args:
        questions (list): List of question objects
    """
    if not questions:
        st.warning("No question data available")
        return
    
    # Count source files
    source_files = [q.get('source_file', 'Unknown') for q in questions]
    source_counts = Counter(source_files)
    
    # Create a DataFrame for the plot
    df = pd.DataFrame({
        'Source File': list(source_counts.keys()),
        'Count': list(source_counts.values())
    }).sort_values('Count', ascending=False)
    
    # Create a bar chart
    fig = px.bar(
        df, 
        x='Source File', 
        y='Count',
        title='Questions by Source File',
        color='Source File',
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    fig.update_layout(
        xaxis_title="Source File",
        yaxis_title="Number of Questions",
        autosize=True,
        margin=dict(l=20, r=20, t=40, b=20),
    )
    
    st.plotly_chart(fig, use_container_width=True)