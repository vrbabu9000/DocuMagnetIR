import asyncio
import os
from pathlib import Path
from main.extraction.syllabus_extractor import SyllabusExtractor
from main.extraction.syllabus_post_process import SyllabusPostProcessor

async def process_syllabus_documents():
    """
    Main function to process syllabus documents:
    1. Extract text from syllabus PDFs using Mathpix API
    2. Post-process the extracted text with Claude API to structure the data (one file at a time)
    """
    # Get the absolute path to the project root directory
    # This assumes main_syllabus_extraction.py is in the same directory level as other scripts
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent  # Go up one level 
    
    print(f"Project root: {project_root}")
    
    # Step 1: Extract syllabus PDFs with Mathpix
    print("\n" + "="*80)
    print("Starting syllabus extraction with Mathpix...")
    print("="*80)
    
    extractor = SyllabusExtractor(project_root=project_root)
    success, failed, skipped = await extractor.run()
    
    print(f"Syllabus extraction completed: {success} successful, {failed} failed, {skipped} skipped")
    
    # Determine if we should continue based on extraction results
    if success == 0 and failed > 0:
        print("No syllabi were successfully extracted. Post-processing will be skipped.")
        return
    
    # Step 2: Post-process extracted syllabi with Claude API (one file at a time)
    print("\n" + "="*80)
    print("Starting syllabus post-processing with Claude API...")
    print("="*80)
    print("Note: Processing files one at a time (no batching)")
    
    processor = SyllabusPostProcessor(root_dir=project_root)
    post_success, post_failed, post_skipped = await processor.run()
    
    print(f"Syllabus post-processing completed: {post_success} successful, {post_failed} failed, {post_skipped} skipped")
    
    # Print summary
    print("\n" + "="*80)
    print("SYLLABUS PROCESSING SUMMARY")
    print("="*80)
    print(f"Extraction: {success} successful, {failed} failed, {skipped} skipped")
    print(f"Post-processing: {post_success} successful, {post_failed} failed, {post_skipped} skipped")
    
    # Get output directory path for reference
    syllabus_output_dir = os.path.join(project_root, "data", "syllabus_extract_ocr")
    print(f"\nResults are available in: {syllabus_output_dir}")
    
    # List processed syllabus folders
    if os.path.exists(syllabus_output_dir):
        syllabus_folders = [f for f in os.listdir(syllabus_output_dir) 
                           if os.path.isdir(os.path.join(syllabus_output_dir, f))]
        
        if syllabus_folders:
            print("\nProcessed syllabi:")
            for folder in syllabus_folders:
                folder_path = os.path.join(syllabus_output_dir, folder)
                json_files = [f for f in os.listdir(folder_path) if f.endswith('_analyzed.json')]
                print(f"  - {folder}: {len(json_files)} analyzed file(s)")

# Execute the function
if __name__ == "__main__":
    asyncio.run(process_syllabus_documents())