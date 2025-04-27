# DocuMagnetIR

**DocuMagnetIR** is a document extraction and question retrieval system designed for academic papers, with specialized support for mathematical notation. It extracts questions from academic PDFs, processes and tags them, and provides a powerful search interface.

## Features

- **PDF Extraction**: Extract questions and content from academic PDFs
- **Mathematical Notation Support**: Render Mathpix Markdown and LaTeX notation
- **Question Tagging**: Automatically tag questions with topics and subtopics
- **Semantic Search**: Find questions based on semantic meaning
- **Topic Visualization**: Visualize question distribution across topics
- **User-Friendly Interface**: Clean Streamlit interface for all functionality

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Data Processing Pipeline](#data-processing-pipeline)
- [Contributing](#contributing)
- [License](#license)

## Installation

### Prerequisites

- Python 3.10.6 or higher
- pip
- virtualenv (recommended)

### Setup

1. Clone the repository
```bash
git clone https://github.com/yourusername/DocuMagnetIR.git
cd DocuMagnetIR
```

2. Create and activate a virtual environment
```bash
python -m venv documag
source documag/bin/activate  # On Windows: documag\Scripts\activate
```

3. Install Python dependencies
```bash
pip install -r requirements.txt
```

## Usage

### Starting the Application

```bash
# from the root folder
streamlit run main/app.py
```

### Workflow

1. **Upload Files**
   - Upload one or more PDF question papers
   - Upload a syllabus PDF

2. **Process Data**
   - Process question documents to extract questions
   - Process syllabus to extract topics and subtopics
   - Generate embeddings for semantic search
   - Tag questions with topics from the syllabus

3. **Visualization**
   - View question type distribution
   - View source distribution
   - Explore topics and subtopics

4. **Search**
   - Use semantic search to find relevant questions
   - Filter by question type, source, or other metadata
   - View questions with properly rendered mathematical notation

5. **Cleanup**
   - Remove processed data if needed

## Project Structure

```
DocuMagnetIR/
├── .streamlit/                # Streamlit configuration
├── data/                      # Data storage directory (All Inputs, OCR Results, Post Processing)
├── documag/                   # Virtual environment
├── main/                      # Main application code
│   ├── embeddings/            # Embedding generation modules
│   ├── extraction/            # Document extraction logics
│   ├── ui/                    # UI components and Streamlit interface
│   └── app.py                 # Main application entry point <--------
├── prompts/                   # Prompt templates
├── results_question_bank/     # Processed question data
├── test_scripts/              # Testing utilities 
├── .env                       # Environment variables (Keys)
├── .gitignore                 # Git ignore file
├── README.md                  # Project documentation
└── requirements.txt           # Python dependencies
```

## Data Processing Pipeline

1. **PDF Extraction**:
   - Extract text from PDF documents
   - Identify questions and their metadata
   - Store in a structured format

2. **Syllabus Processing**:
   - Extract topics and subtopics from syllabus
   - Create a hierarchical structure of course content

3. **Embedding Generation**:
   - Generate vector embeddings for questions
   - Enable semantic search functionality

4. **Question Tagging**:
   - Map questions to topics and subtopics
   - Use semantic similarity to identify topics

5. **Search Indexing**:
   - Create search indices for quick retrieval
   - Support for filtering and advanced queries

## Acknowledgments

- Built with [Streamlit](https://streamlit.io/) for the user interface