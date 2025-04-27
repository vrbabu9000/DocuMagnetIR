import asyncio
import os
from pathlib import Path
from main.extraction.mathpix_extractor import MathpixExtractor
from main.extraction.llm_post_process import ClaudePostProcessor
from main.extraction.question_bank_generator import QuestionBankGenerator
from main.extraction.subquestions_post_process import SubQuestionPostProcessor

async def process_documents(run_subquestion_processing=True):
    """
    Run the complete document processing pipeline.
    
    Args:
        run_subquestion_processing (bool): Whether to run the sub-question independence evaluation
    """
    # Get the absolute path to the project root directory
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent  # Go up three levels from this script
    
    # Create absolute paths for input and output directories
    input_dir = os.path.join(project_root, "data", "sample_papers")
    output_dir = os.path.join(project_root, "data", "ocr_results")
    
    print(f"Project root: {project_root}")
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    
    # Step 1: Extract content from PDFs using Mathpix
    print("\n=== Step 1: OCR Extraction ===")
    extractor = MathpixExtractor(
        input_dir=input_dir,
        output_dir=output_dir
    )
    
    # Run the extraction process
    ocr_success, ocr_failed, ocr_skipped = await extractor.run()
    print(f"OCR extraction completed: {ocr_success} successful, {ocr_failed} failed, {ocr_skipped} skipped")
    
    # Step 2: Run the initial Claude post-processing to identify questions
    print("\n=== Step 2: Initial Question Identification ===")
    processor = ClaudePostProcessor(root_dir=project_root)
    post_success, post_failed, post_skipped = await processor.run()
    print(f"Initial post-processing completed: {post_success} successful, {post_failed} failed, {post_skipped} skipped")
    
    # Step 3: Generate the question bank
    print("\n=== Step 3: Question Bank Generation ===")
    generator = QuestionBankGenerator(root_dir=project_root)
    output_path, num_questions = generator.run()
    print(f"Question bank generation completed: {num_questions} questions extracted")
    print(f"Question bank saved to: {output_path}")
    
    # Step 4 (optional): Run sub-question independence evaluation
    if run_subquestion_processing:
        print("\n=== Step 4: Sub-Question Independence Evaluation ===")
        subq_processor = SubQuestionPostProcessor(root_dir=project_root)
        processed, updated, extracted = await subq_processor.run_async()
        print(f"Sub-question post-processing completed: {processed} questions processed")
        print(f"  - {updated} questions had independence flag updated")
        print(f"  - {extracted} sub-questions were extracted")
    
    print("\n=== Pipeline Execution Complete ===")

async def run_only_subquestion_processing():
    """Run only the sub-question independence evaluation step."""
    # Get the absolute path to the project root directory
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent  # Go up three levels from this script
    
    print(f"Project root: {project_root}")
    
    # Run sub-question independence evaluation
    print("\n=== Running Sub-Question Independence Evaluation ===")
    subq_processor = SubQuestionPostProcessor(root_dir=project_root)
    # Call the async method directly instead of the run() wrapper
    processed, updated, extracted = await subq_processor.run_async()
    print(f"Sub-question post-processing completed: {processed} questions processed")
    print(f"  - {updated} questions had independence flag updated")
    print(f"  - {extracted} sub-questions were extracted")

if __name__ == "__main__":
    import sys
    
    # Check command-line arguments to determine what to run
    if len(sys.argv) > 1:
        if sys.argv[1] == "--subq-only":
            # Run only the sub-question processing step
            asyncio.run(run_only_subquestion_processing())
        elif sys.argv[1] == "--no-subq":
            # Run the pipeline without sub-question processing
            asyncio.run(process_documents(run_subquestion_processing=False))
        elif sys.argv[1] == "--help":
            print("Usage: python main_questions_extraction.py [OPTION]")
            print("\nOptions:")
            print("  --subq-only : Run only the sub-question independence evaluation")
            print("  --no-subq   : Run the pipeline without sub-question processing")
            print("  --help      : Show this help message")
            print("  (no args)   : Run the complete pipeline")
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print("Use --help to see available options")
    else:
        # Run the complete pipeline by default
        asyncio.run(process_documents())