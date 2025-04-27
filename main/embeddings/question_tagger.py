"""
Question Topic Tagger

This script automatically tags questions with relevant subtopics from a syllabus
based on semantic similarity. It uses pre-generated question embeddings and
generates embeddings for syllabus subtopics using the same model.

The script produces a JSON file organizing questions by main topic and subtopic.
"""

import os
import json
import pickle
import numpy as np
from typing import List, Dict, Any, Tuple
from pathlib import Path
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

class QuestionTopicTagger:
    """
    A class to tag questions with relevant subtopics from a syllabus based on
    semantic similarity.
    """
    
    def __init__(
        self,
        question_embedding_path: str,
        question_metadata_path: str,
        syllabus_path: str,
        model_name: str = "all-MiniLM-L6-v2",
        output_path: str = "tagged_questions.json",
        max_tags: int = 3
    ):
        """
        Initialize the question topic tagger.
        
        Args:
            question_embedding_path: Path to the pre-generated question embeddings
            question_metadata_path: Path to the question metadata
            syllabus_path: Path to the syllabus JSON file
            model_name: Name of the sentence transformer model to use
            output_path: Path to save the output JSON
            max_tags: Maximum number of subtopic tags per question
        """
        self.question_embedding_path = question_embedding_path
        self.question_metadata_path = question_metadata_path
        self.syllabus_path = syllabus_path
        self.model_name = model_name
        self.output_path = output_path
        self.max_tags = max_tags
        
        self.model = None
        self.question_embeddings = None
        self.question_metadata = None
        self.syllabus_data = None
        self.subtopic_embeddings = None
        self.subtopic_info = None
        
    def load_question_data(self) -> Tuple[np.ndarray, List[Dict]]:
        """
        Load the pre-generated question embeddings and metadata.
        
        Returns:
            Tuple of (embeddings array, metadata list)
        """
        print(f"Loading question embeddings from {self.question_embedding_path}")
        with open(self.question_embedding_path, 'rb') as f:
            self.question_embeddings = pickle.load(f)
            
        print(f"Loading question metadata from {self.question_metadata_path}")
        with open(self.question_metadata_path, 'r', encoding='utf-8') as f:
            self.question_metadata = json.load(f)
            
        return self.question_embeddings, self.question_metadata
    
    def load_syllabus(self) -> Dict:
        """
        Load the syllabus data from the JSON file.
        
        Returns:
            Dictionary containing syllabus data
        """
        print(f"Loading syllabus data from {self.syllabus_path}")
        with open(self.syllabus_path, 'r', encoding='utf-8') as f:
            self.syllabus_data = json.load(f)
        
        return self.syllabus_data
    
    def generate_subtopic_embeddings(self) -> Tuple[np.ndarray, List[Dict]]:
        """
        Generate embeddings for each subtopic in the syllabus.
        
        Returns:
            Tuple of (subtopic embeddings array, subtopic info list)
        """
        if self.model is None:
            print(f"Loading SBERT model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
        
        if self.syllabus_data is None:
            self.load_syllabus()
        
        print("Generating embeddings for syllabus subtopics...")
        subtopics = []
        subtopic_info = []
        
        # For each main topic and its subtopics in the syllabus
        for topic_idx, topic in enumerate(self.syllabus_data["topics"]):
            topic_name = topic["name"]
            
            for subtopic_idx, subtopic in enumerate(topic["subtopics"]):
                # Create an integrated text with the main topic for better context
                integrated_text = f"{topic_name}: {subtopic}"
                subtopics.append(integrated_text)
                
                # Store info about the subtopic
                subtopic_info.append({
                    "main_topic": topic_name,
                    "subtopic": subtopic,
                    "main_topic_idx": topic_idx,
                    "subtopic_idx": subtopic_idx
                })
        
        # Generate embeddings for all subtopics
        subtopic_embeddings = self.model.encode(subtopics, show_progress_bar=True)
        
        self.subtopic_embeddings = subtopic_embeddings
        self.subtopic_info = subtopic_info
        
        return subtopic_embeddings, subtopic_info
    
    def calculate_similarity(self, question_embedding: np.ndarray, subtopic_embeddings: np.ndarray) -> np.ndarray:
        """
        Calculate cosine similarity between a question embedding and all subtopic embeddings.
        
        Args:
            question_embedding: Embedding vector for a question
            subtopic_embeddings: Array of embedding vectors for subtopics
            
        Returns:
            Array of similarity scores
        """
        # Calculate cosine similarity
        similarities = np.dot(subtopic_embeddings, question_embedding) / (
            np.linalg.norm(subtopic_embeddings, axis=1) * np.linalg.norm(question_embedding)
        )
        
        return similarities
    
    def assign_subtopic_tags(self) -> List[Dict]:
        """
        Assign subtopic tags to each question based on semantic similarity.
        
        Returns:
            List of questions with assigned tags
        """
        if self.question_embeddings is None or self.question_metadata is None:
            self.load_question_data()
            
        if self.subtopic_embeddings is None or self.subtopic_info is None:
            self.generate_subtopic_embeddings()
        
        print("Assigning subtopic tags to questions...")
        tagged_questions = []
        
        for idx, question_meta in enumerate(tqdm(self.question_metadata)):
            question_embedding = self.question_embeddings[idx]
            
            # Calculate similarity with all subtopics
            similarities = self.calculate_similarity(question_embedding, self.subtopic_embeddings)
            
            # Get top k similar subtopics
            top_indices = np.argsort(-similarities)[:self.max_tags]
            
            # Create tags from top subtopics
            tags = []
            for i in top_indices:
                tags.append({
                    "main_topic": self.subtopic_info[i]["main_topic"],
                    "subtopic": self.subtopic_info[i]["subtopic"],
                    "similarity_score": float(similarities[i])
                })
            
            # Add tags to question metadata
            tagged_question = question_meta.copy()
            tagged_question["tags"] = tags
            tagged_questions.append(tagged_question)
        
        return tagged_questions
    
    def organize_by_topic(self, tagged_questions: List[Dict]) -> Dict:
        """
        Organize tagged questions by main topic and subtopic.
        
        Args:
            tagged_questions: List of questions with assigned tags
            
        Returns:
            Dictionary organizing questions by topic and subtopic
        """
        organized_data = {
            "course_name": self.syllabus_data["course_name"],
            "topics": []
        }
        
        # Create a structure for the topics
        topic_map = {}
        for topic_idx, topic in enumerate(self.syllabus_data["topics"]):
            topic_name = topic["name"]
            topic_map[topic_name] = {
                "name": topic_name,
                "subtopics": {},
                "index": topic_idx
            }
            
            # Initialize subtopics
            for subtopic in topic["subtopics"]:
                topic_map[topic_name]["subtopics"][subtopic] = []
        
        # Assign questions to their most relevant subtopic within the most relevant main topic
        for question in tagged_questions:
            # Skip if no tags
            if not question["tags"]:
                continue
            
            # Group tags by main topic and find the most relevant main topic
            topic_scores = {}
            for tag in question["tags"]:
                main_topic = tag["main_topic"]
                if main_topic not in topic_scores:
                    topic_scores[main_topic] = tag["similarity_score"]
                else:
                    topic_scores[main_topic] = max(topic_scores[main_topic], tag["similarity_score"])
            
            # Get the main topic with the highest similarity score
            top_main_topic = max(topic_scores.items(), key=lambda x: x[1])[0]
            
            # Filter tags to only include subtopics from the top main topic
            filtered_tags = [tag for tag in question["tags"] if tag["main_topic"] == top_main_topic]
            
            # Use the top tag within the filtered tags
            if filtered_tags:
                top_tag = filtered_tags[0]
                main_topic = top_tag["main_topic"]
                subtopic = top_tag["subtopic"]
                
                # Add question to appropriate subtopic
                if main_topic in topic_map and subtopic in topic_map[main_topic]["subtopics"]:
                    topic_map[main_topic]["subtopics"][subtopic].append({
                        "question_number": question["question_number"],
                        "question_text": question["original_object"]["question_text"],
                        "question_type": question["question_type"],
                        "all_tags": filtered_tags,  # Only include tags from the top main topic
                        "source_file": question["source_file"]
                    })
        
        # Convert the map to a list structure for the final output
        topics_list = sorted(topic_map.values(), key=lambda x: x["index"])
        for topic in topics_list:
            subtopics_list = []
            for subtopic_name, questions in topic["subtopics"].items():
                if questions:  # Only include subtopics with questions
                    subtopics_list.append({
                        "name": subtopic_name,
                        "questions": questions
                    })
            
            # Remove the index and subtopics map
            del topic["index"]
            del topic["subtopics"]
            
            # Add the list of subtopics
            topic["subtopics"] = subtopics_list
            
            # Only add topics that have questions
            if any(subtopic["questions"] for subtopic in subtopics_list):
                organized_data["topics"].append(topic)
        
        return organized_data
    
    def save_tagged_questions(self, organized_data: Dict) -> None:
        """
        Save the organized questions to a JSON file.
        
        Args:
            organized_data: Dictionary organizing questions by topic and subtopic
        """
        print(f"Saving tagged questions to {self.output_path}")
        os.makedirs(os.path.dirname(self.output_path) if os.path.dirname(self.output_path) else '.', exist_ok=True)
        
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(organized_data, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully saved tagged questions to {self.output_path}")
    
    def run(self) -> Dict:
        """
        Run the complete tagging process from loading data to saving results.
        
        Returns:
            Dictionary organizing questions by topic and subtopic
        """
        # Load data
        self.load_question_data()
        self.load_syllabus()
        
        # Generate subtopic embeddings
        self.generate_subtopic_embeddings()
        
        # Tag questions with subtopics
        tagged_questions = self.assign_subtopic_tags()
        
        # Organize by topic and subtopic
        organized_data = self.organize_by_topic(tagged_questions)
        
        # Save the results
        self.save_tagged_questions(organized_data)
        
        return organized_data


def main():
    """Main function to run the question topic tagger."""
    
    # Define paths
    base_dir = Path("D:/MSE_DS_JHU/Semester1/Information_Retrieval_Web_Agents/Git/DocuMagnetIR")
    
    question_embedding_path = base_dir / "main/embeddings/question_embeddings.pkl"
    question_metadata_path = base_dir / "main/embeddings/question_metadata.json"
    syllabus_path = base_dir / "data/syllabus_extract_ocr/cs466_Syllabus/cs466_Syllabus_analyzed.json"
    output_path = base_dir / "results_question_bank/tagged_questions.json"
    
    # Create and run the tagger
    tagger = QuestionTopicTagger(
        question_embedding_path=str(question_embedding_path),
        question_metadata_path=str(question_metadata_path),
        syllabus_path=str(syllabus_path),
        output_path=str(output_path)
    )
    
    organized_data = tagger.run()
    
    # Print some statistics
    topic_count = len(organized_data["topics"])
    question_count = sum(
        len(question_list["questions"]) 
        for topic in organized_data["topics"] 
        for question_list in topic["subtopics"]
    )
    
    print(f"\nTagging complete!")
    print(f"Tagged {question_count} questions across {topic_count} topics")
    print(f"Results saved to {output_path}")


if __name__ == "__main__":
    main()