import asyncio
import os
from pathlib import Path
from mathpix_extractor import MathpixExtractor

# For a script that runs directly
async def process_documents():
    # Get the absolute path to the project root directory
    # This assumes main.py is in the 'main' folder of your project
    current_file = Path(__file__)
    project_root = current_file.parent.parent  # Go up one level from main.py
    
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

# Execute the function
if __name__ == "__main__":
    asyncio.run(process_documents())