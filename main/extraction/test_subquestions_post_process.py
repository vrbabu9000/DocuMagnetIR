import os
import sys
import json
from pathlib import Path
from subquestions_post_process import SubQuestionPostProcessor


def test_with_sample_question():
    """
    Test the SubQuestionPostProcessor with a sample question.
    This is useful for debugging and testing without modifying the actual question bank.
    """
    # Sample question with independent sub-questions
    sample_question = {
        "question_number": "test",
        "question_text": "\\section{$4$ Clustering (10 pts)}\n1. [4pts] Calculate purity and Rand Index of the following two clusterings. $D_{i}$ 's are documents and $C_{i}$ 's are classes. (Purity of a clustering is an average of purity of individual clusters.) The true labels of the documents are:\n$\\left\\{\\left(D_{1}: C_{1}\\right),\\left(D_{2}: C_{2}\\right),\\left(D_{3}: C_{1}\\right),\\left(D_{4}: C_{1}\\right),\\left(D_{5}: C_{2}\\right)\\right\\}$\n\n\\section{Clustering 1:}\n\nCluster 1: $D_{1}$\nCluster 2: $D_{2}$\nCluster 3: $D_{3}$\nCluster 4: $D_{4}$\nCluster 5: $D_{5}$\n\n\\section{Clustering 2:}\n\nCluster 1: $D_{1}, D_{2}, D_{3}, D_{4}$\nCluster 2: $D_{5}$\n\nPurity:\nRand Index:\n\nPurity:\nRand Index:\n2. [2pts] Is purity a good evaluation measure by itself? In 1-2 sentences write why or why not.\n3. [4pts] Each iteration of K-means can be run using the Map-Reduce framework. Write down in 1-2 sentences what would be the (key, value) pairs in the map and the reduce step.\n\nMap step:\n\nReduce step:\n",
        "question_type": "Mixed",
        "sub_questions_independent": True,
        "source_pdf": "test_pdf",
        "source_file": "test_file.mmd"
    }
    
    # Initialize the processor
    processor = SubQuestionPostProcessor()
    
    # Now test the evaluation method
    print("Testing question independence evaluation...")
    result = processor._evaluate_question_independence(sample_question["question_text"])
    
    print("\nClaude evaluation result:")
    print(json.dumps(result, indent=2))
    
    if result and result.get("sub_questions_independent", False):
        question_starts = result.get("question_starts", [])
        print(f"\nIdentified {len(question_starts)} sub-question starts:")
        for start in question_starts:
            print(f"  - {start}")
        
        # Test sub-question extraction
        sub_questions = processor._extract_sub_questions(sample_question["question_text"], question_starts)
        print(f"\nExtracted {len(sub_questions)} complete sub-questions:")
        
        # Print each sub-question with clear boundaries
        for i, sub_q in enumerate(sub_questions):
            print(f"\n{'='*80}")
            print(f"SUB-QUESTION {i+1} START")
            print(f"{'='*80}")
            print(sub_q)
            print(f"{'='*80}")
            print(f"SUB-QUESTION {i+1} END")
            print(f"{'='*80}")
    else:
        print("\nQuestion was evaluated as NOT having independent sub-questions")


def backup_question_bank():
    """
    Create a backup of the question bank before running the processor.
    """
    # Get the project root
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent  # Go up three levels from this script
    
    # Set up file paths
    question_bank_path = os.path.join(project_root, "results_question_bank", "question_bank.json")
    backup_path = os.path.join(project_root, "results_question_bank", "question_bank_backup.json")
    
    try:
        # Read the current question bank
        with open(question_bank_path, 'r', encoding='utf-8') as file:
            question_bank = json.load(file)
        
        # Save a backup
        with open(backup_path, 'w', encoding='utf-8') as file:
            json.dump(question_bank, file, indent=2)
        
        print(f"Created backup of question bank at: {backup_path}")
        return True
    except Exception as e:
        print(f"Error creating backup: {str(e)}")
        return False


def run_processor():
    """
    Run the SubQuestionPostProcessor on the actual question bank.
    """
    processor = SubQuestionPostProcessor()
    processed, updated, extracted = processor.run()
    print(f"Sub-question post-processing completed: {processed} questions processed")
    print(f"  - {updated} questions had independence flag updated")
    print(f"  - {extracted} sub-questions were extracted")


if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test":
            print("Running test with sample question...")
            test_with_sample_question()
        elif sys.argv[1] == "--backup":
            print("Creating backup of question bank...")
            backup_question_bank()
        elif sys.argv[1] == "--help":
            print("Usage options:")
            print("  --test    : Run a test with a sample question without modifying the question bank")
            print("  --backup  : Create a backup of the question bank")
            print("  --run     : Run the processor on the actual question bank (creates backup automatically)")
            print("  --help    : Show this help message")
            print("  (no args) : Show this help message")
        elif sys.argv[1] == "--run":
            print("Running the sub-question post-processor...")
            if backup_question_bank():
                run_processor()
            else:
                print("Aborting: Failed to create backup of question bank")
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print("Use --help to see available options")
    else:
        print("Please specify an option:")
        print("  --test    : Run a test with a sample question")
        print("  --backup  : Create a backup of the question bank")
        print("  --run     : Run the processor on the actual question bank")
        print("  --help    : Show detailed help")