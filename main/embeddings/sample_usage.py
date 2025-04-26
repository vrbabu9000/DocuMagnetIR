"""
Example usage of the QuestionEmbeddingGenerator class

This script demonstrates how to use the QuestionEmbeddingGenerator class
to generate embeddings for a question bank and search for similar questions.
"""

import os
from question_embedding_generator import QuestionEmbeddingGenerator

def main():
    # Define paths
    question_bank_path = "D:/MSE_DS_JHU/Semester1/Information_Retrieval_Web_Agents/Git/DocuMagnetIR/results_question_bank/question_bank.json"
    output_dir = "D:/MSE_DS_JHU/Semester1/Information_Retrieval_Web_Agents/Git/DocuMagnetIR/main/embeddings"
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize the generator
    generator = QuestionEmbeddingGenerator(
        model_name="all-MiniLM-L6-v2",  # You can change to a more powerful model if needed
        embedding_path=os.path.join(output_dir, "question_embeddings.pkl"),
        metadata_path=os.path.join(output_dir, "question_metadata.json")
    )
    
    # Process the question bank (will only regenerate if needed)
    embeddings, metadata = generator.process_question_bank(question_bank_path)
    
    print(f"Working with embeddings for {len(metadata)} questions")
    print(f"Embedding dimension: {embeddings.shape[1]}")
    
    # If you want to force regeneration (e.g., when changing models)
    # Uncomment the line below
    # embeddings, metadata = generator.process_question_bank(question_bank_path, force_regenerate=True)
    
    # Example of searching for similar questions
    search_query = "Web crawlers and their applications"
    similar_questions = generator.search_similar_questions(search_query, top_k=3)
    
    print("\nExample search results:")
    print(f"Query: '{search_query}'")
    print("Top 3 similar questions:")
    
    for i, result in enumerate(similar_questions, 1):
        print(f"\n{i}. Question {result['question_number']} (Score: {result['similarity_score']:.4f})")
        print(f"Type: {result['question_type']}")
        print(f"Source: {result['source_file']}")
        
        # Print a snippet of the question text
        question_text = result['original_object'].get('question_text', '')
        if len(question_text) > 100:
            question_text = question_text[:100] + "..."
        print(f"Text: {question_text}")

if __name__ == "__main__":
    main()