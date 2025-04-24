import asyncio
import os
from pathlib import Path
from mathpix_extractor import MathpixExtractor
from llm_post_process import ClaudePostProcessor
from question_bank_generator import QuestionBankGenerator

# For a script that runs directly
async def process_documents():
    # Get the absolute path to the project root directory
    # This assumes main.py is in the 'main' folder of your project
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent  # Go up one level from main.py
    
    # Create absolute paths for input and output directories
    input_dir = os.path.join(project_root, "data", "sample_papers")
    output_dir = os.path.join(project_root, "data", "ocr_results")
    
    print(f"Project root: {project_root}")
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    
    # Create an instance with absolute paths
    extractor = MathpixExtractor(
        input_dir=input_dir,
        output_dir=output_dir
    )
    
    # Run the extraction process
    success, failed, skipped = await extractor.run()
    print(f"Processed documents: {success} successful, {failed} failed, {skipped} skipped")
    
    # Run the post-processing with Claude
    print("\nStarting Claude post-processing...")
    processor = ClaudePostProcessor(root_dir=project_root)
    post_success, post_failed, post_skipped = await processor.run()
    print(f"Post-processing completed: {post_success} successful, {post_failed} failed, {post_skipped} skipped")
    
    # Generate the question bank
    print("\nStarting question bank generation...")
    generator = QuestionBankGenerator(root_dir=project_root)
    output_path, num_questions = generator.run()
    print(f"Question bank generation completed: {num_questions} questions extracted")
    print(f"Question bank saved to: {output_path}")

# Execute the function
if __name__ == "__main__":
    asyncio.run(process_documents())