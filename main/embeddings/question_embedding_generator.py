"""
Question Embedding Generator

This module provides a class for generating embeddings for questions in a question bank
using sentence transformers, while preserving metadata for each question.
"""

import json
import os
import pickle
from typing import List, Dict, Any, Tuple, Optional, Union

import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

class QuestionEmbeddingGenerator:
    """
    A class to generate and manage embeddings for a question bank.
    
    This class handles loading questions, generating embeddings, storing metadata,
    and providing search functionality for similar questions.
    """
    
    def __init__(
        self, 
        model_name: str = "all-MiniLM-L6-v2", 
        embedding_path: str = "question_embeddings.pkl",
        metadata_path: str = "question_metadata.json"
    ):
        """
        Initialize the question embedding generator.
        
        Args:
            model_name: Name of the sentence transformer model to use
            embedding_path: Path to save/load embeddings
            metadata_path: Path to save/load metadata
        """
        self.model_name = model_name
        self.embedding_path = embedding_path
        self.metadata_path = metadata_path
        self.model = None
        self.embeddings = None
        self.metadata = None
        
    def load_question_bank(self, json_str_or_file: str) -> List[Dict[Any, Any]]:
        """
        Load question bank from a JSON string or file.
        
        Args:
            json_str_or_file: JSON string or path to JSON file
            
        Returns:
            List of question dictionaries
            
        Raises:
            ValueError: If input is not a valid JSON string or file path
        """
        try:
            # First try to parse as a string
            return json.loads(json_str_or_file)
        except (json.JSONDecodeError, TypeError):
            # If that fails, treat as a file path
            try:
                with open(json_str_or_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                raise ValueError("Input must be valid JSON string or path to JSON file")
    
    def _get_integrated_text(self, question_dict: Dict) -> str:
        """
        Create an integrated text representation of the question that includes
        the question_type as context for the embedding.
        
        Args:
            question_dict: Dictionary containing question information
            
        Returns:
            Integrated text string combining question text and type
        """
        question_text = question_dict.get("question_text", "")
        question_type = question_dict.get("question_type", "Unknown")
        
        # Integrate question type with question text
        integrated_text = f"[{question_type}] {question_text}"
        
        return integrated_text
    
    def generate_embeddings(self, questions: List[Dict]) -> Tuple[np.ndarray, List[Dict]]:
        """
        Generate embeddings for each question in the question bank.
        
        Args:
            questions: List of question dictionaries
            
        Returns:
            Tuple of (embeddings array, metadata list)
        """
        print(f"Loading SBERT model: {self.model_name}")
        if self.model is None:
            self.model = SentenceTransformer(self.model_name)
        
        # Create integrated texts for embedding
        integrated_texts = [self._get_integrated_text(q) for q in questions]
        
        print(f"Generating embeddings for {len(questions)} questions...")
        embeddings = self.model.encode(integrated_texts, show_progress_bar=True)
        
        # Create metadata for each question
        metadata = []
        for i, question in enumerate(questions):
            metadata.append({
                "index": i,
                "question_number": question.get("question_number"),
                "question_type": question.get("question_type"),
                "sub_questions_independent": question.get("sub_questions_independent"),
                "source_pdf": question.get("source_pdf"),
                "source_file": question.get("source_file"),
                "original_object": question
            })
        
        self.embeddings = embeddings
        self.metadata = metadata
        
        return embeddings, metadata
    
    def save(self, 
             emb_path: Optional[str] = None, 
             meta_path: Optional[str] = None) -> None:
        """
        Save embeddings array and metadata to disk.
        
        Args:
            emb_path: Path to save embeddings (defaults to self.embedding_path)
            meta_path: Path to save metadata (defaults to self.metadata_path)
            
        Raises:
            ValueError: If embeddings or metadata haven't been generated yet
        """
        if self.embeddings is None or self.metadata is None:
            raise ValueError("No embeddings or metadata to save. Generate embeddings first.")
        
        emb_path = emb_path or self.embedding_path
        meta_path = meta_path or self.metadata_path
        
        # Create directories if they don't exist
        os.makedirs(os.path.dirname(emb_path) if os.path.dirname(emb_path) else '.', exist_ok=True)
        os.makedirs(os.path.dirname(meta_path) if os.path.dirname(meta_path) else '.', exist_ok=True)
        
        # Save embeddings
        with open(emb_path, 'wb') as f:
            pickle.dump(self.embeddings, f)
        
        # Save metadata
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2)
        
        print(f"Saved embeddings to {emb_path}")
        print(f"Saved metadata to {meta_path}")
    
    def load(self, 
             emb_path: Optional[str] = None, 
             meta_path: Optional[str] = None) -> Tuple[np.ndarray, List[Dict]]:
        """
        Load embeddings and metadata from disk.
        
        Args:
            emb_path: Path to load embeddings from (defaults to self.embedding_path)
            meta_path: Path to load metadata from (defaults to self.metadata_path)
            
        Returns:
            Tuple of (embeddings array, metadata list)
            
        Raises:
            FileNotFoundError: If embedding or metadata files don't exist
        """
        emb_path = emb_path or self.embedding_path
        meta_path = meta_path or self.metadata_path
        
        # Load embeddings
        if not os.path.exists(emb_path):
            raise FileNotFoundError(f"Embedding file not found: {emb_path}")
        
        with open(emb_path, 'rb') as f:
            self.embeddings = pickle.load(f)
        
        # Load metadata
        if not os.path.exists(meta_path):
            raise FileNotFoundError(f"Metadata file not found: {meta_path}")
        
        with open(meta_path, 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)
        
        print(f"Loaded embeddings from {emb_path}")
        print(f"Loaded metadata from {meta_path}")
        
        return self.embeddings, self.metadata
    
    def search_similar_questions(self, 
                               query: str, 
                               top_k: int = 5) -> List[Dict]:
        """
        Find questions similar to the query text.
        
        Args:
            query: Query text to find similar questions for
            top_k: Number of top results to return
            
        Returns:
            List of dictionaries containing metadata and similarity scores
            
        Raises:
            ValueError: If embeddings haven't been generated or loaded yet
        """
        if self.embeddings is None or self.metadata is None:
            raise ValueError("No embeddings or metadata available. Generate or load embeddings first.")
        
        if self.model is None:
            self.model = SentenceTransformer(self.model_name)
        
        # Generate embedding for the query
        query_embedding = self.model.encode(query)
        
        # Calculate cosine similarity
        similarities = np.dot(self.embeddings, query_embedding) / (
            np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_embedding)
        )
        
        # Get top-k indices
        top_indices = np.argsort(-similarities)[:top_k]
        
        # Prepare results
        results = []
        for idx in top_indices:
            result = self.metadata[idx].copy()
            result["similarity_score"] = float(similarities[idx])
            results.append(result)
        
        return results
    
    def process_question_bank(self, question_bank_data: str, force_regenerate: bool = False) -> Tuple[np.ndarray, List[Dict]]:
        """
        Process a question bank from start to finish.
        
        This method will check if embeddings already exist and only regenerate them if:
        1. They don't exist
        2. The question bank has changed
        3. force_regenerate is True
        
        Args:
            question_bank_data: JSON string or path containing question bank data
            force_regenerate: If True, regenerate embeddings even if they exist
            
        Returns:
            Tuple of (embeddings array, metadata list)
        """
        # Load questions
        questions = self.load_question_bank(question_bank_data)
        print(f"Loaded {len(questions)} questions from question bank")
        
        # Check if we need to regenerate embeddings
        regenerate = force_regenerate
        
        if not regenerate and os.path.exists(self.embedding_path) and os.path.exists(self.metadata_path):
            try:
                # Load existing embeddings
                self.load()
                
                # Check if the number of questions matches
                if len(self.metadata) != len(questions):
                    print("Question count has changed. Regenerating embeddings...")
                    regenerate = True
                else:
                    # Verify if question content has changed by checking a sample of questions
                    # This is a simple heuristic that could be improved with a more robust hash-based approach
                    for i in range(min(10, len(questions))):
                        meta_question = self.metadata[i]["original_object"]["question_text"]
                        current_question = questions[i]["question_text"]
                        if meta_question != current_question:
                            print("Question content has changed. Regenerating embeddings...")
                            regenerate = True
                            break
                    
                    if not regenerate:
                        print("Using existing embeddings (no changes detected)")
                        return self.embeddings, self.metadata
            except Exception as e:
                print(f"Error loading existing embeddings: {e}")
                print("Will regenerate embeddings")
                regenerate = True
        else:
            print("No existing embeddings found. Generating new embeddings...")
            regenerate = True
        
        # Generate embeddings and metadata if needed
        if regenerate:
            embeddings, metadata = self.generate_embeddings(questions)
            
            # Save to disk
            self.save()
            
            print(f"Successfully generated embeddings with shape: {embeddings.shape}")
            print(f"Each question has an embedding dimension of {embeddings.shape[1]}")
            
            return embeddings, metadata
        
        return self.embeddings, self.metadata


def main():
    """Example usage of the QuestionEmbeddingGenerator class."""
    import sys
    
    if len(sys.argv) > 1:
        question_bank_file = sys.argv[1]
        
        # Initialize the generator
        generator = QuestionEmbeddingGenerator(
            model_name="all-MiniLM-L6-v2",
            embedding_path="outputs/question_embeddings.pkl",
            metadata_path="outputs/question_metadata.json"
        )
        
        # Process the question bank
        generator.process_question_bank(question_bank_file)
    else:
        print("Please provide the question bank JSON file path as an argument")


if __name__ == "__main__":
    main()