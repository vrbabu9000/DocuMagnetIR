import os
import asyncio
import httpx
import traceback
from pathlib import Path
from mathpix_extractor import MathpixExtractor


class SyllabusExtractor(MathpixExtractor):
    """
    A specialized class for extracting text from syllabus PDFs using Mathpix API.
    Inherits from MathpixExtractor and customizes the workflow for syllabus documents.
    """
    
    def __init__(self, project_root=None):
        """
        Initialize the SyllabusExtractor with syllabus-specific paths.
        
        Args:
            project_root (str): Root directory of the project (optional)
        """
        # Determine project root if not provided
        if not project_root:
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent  # Assuming this file is in main/extraction
        
        # Create paths for syllabus input and regular output
        syllabus_input_dir = os.path.join(project_root, "data", "syllabus")
        parent_output_dir = os.path.join(project_root, "data", "ocr_results")
        
        # Create syllabus-specific output directory at same level as ocr_results
        self.syllabus_output_dir = os.path.join(os.path.dirname(parent_output_dir), "syllabus_extract_ocr")
        
        # Initialize the parent class with syllabus paths but use regular output dir for processed_files.json
        super().__init__(input_dir=syllabus_input_dir, output_dir=parent_output_dir)
        os.makedirs(self.syllabus_output_dir, exist_ok=True)
    
    async def get_syllabus_files(self):
        """
        Get a list of syllabus PDF files from the syllabus directory.
        
        Returns:
            list: List of paths to syllabus PDF files
        """
        pdf_files = []
        
        if not os.path.exists(self.input_dir):
            print(f"Syllabus directory not found: {self.input_dir}")
            return []
        
        for root, _, files in os.walk(self.input_dir):
            for file in files:
                if file.lower().endswith('.pdf'):
                    pdf_files.append(os.path.join(root, file))
        
        return pdf_files
    
    async def download_md_only(self, pdf_id, output_dir, file_name):
        """
        Download only the MD format from Mathpix API.
        
        Args:
            pdf_id (str): The ID of the processed PDF
            output_dir (str): Directory to save downloaded format
            file_name (str): Base name for output file
            
        Returns:
            bool: True if download was successful, False otherwise
        """
        print(f"Waiting for processing to complete before downloading MD format...")
        
        # Wait for processing to complete
        processing_complete = await self.wait_for_processing(pdf_id)
        if not processing_complete:
            print("Processing did not complete. MD format may not be available.")
            return False
        
        print(f"Downloading MD format for PDF ID: {pdf_id}")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        url = f"{self.BASE_URL}/{pdf_id}.md"
        headers = {"app_key": self.app_key}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    output_path = os.path.join(output_dir, f"{file_name}.md")
                    
                    # Save the content
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(response.text)
                    
                    print(f"Downloaded MD format to {output_path}")
                    return True
                else:
                    print(f"Failed to download MD format: {response.status_code}, {response.text}")
                    return False
        except Exception as e:
            print(f"Error downloading MD format: {e}")
            import traceback
            print(traceback.format_exc())
            return False
    
    async def process_syllabus(self, file_path):
        """
        Process a single syllabus PDF file with Mathpix.
        
        Args:
            file_path (str): Path to the syllabus PDF file
            
        Returns:
            bool: True if processing was successful, False otherwise
        """
        print(f"\n{'='*80}\nProcessing Syllabus PDF: {file_path}\n{'='*80}")
        
        file_name = Path(file_path).stem
        
        # Create the syllabus output directory path
        syllabus_output_dir = os.path.join(self.syllabus_output_dir, file_name)
        os.makedirs(syllabus_output_dir, exist_ok=True)
        
        # Check if this file has already been processed
        relative_path = os.path.relpath(file_path, self.input_dir)
        syllabus_key = f"syllabus:{relative_path}"
        
        if syllabus_key in self.processed_files:
            pdf_id = self.processed_files[syllabus_key]
            print(f"Syllabus PDF {file_path} was already processed with ID: {pdf_id}")
            
            # Check if results exist
            if os.path.exists(os.path.join(syllabus_output_dir, f"{file_name}.md")):
                print("Results already exist. Skipping processing.")
                return True
            else:
                print("Results not found. Re-downloading MD format...")
                await self.download_md_only(pdf_id, syllabus_output_dir, file_name)
                return True
        
        # 1. Upload the PDF
        pdf_id = await self.upload_pdf_file(file_path)
        if not pdf_id:
            return False
        
        # 2. Download only the MD format
        success = await self.download_md_only(pdf_id, syllabus_output_dir, file_name)
        
        # 3. Update the processed files map
        if success:
            self.processed_files[syllabus_key] = pdf_id
            self._save_processed_files()
        
        return success
    
    async def run(self):
        """
        Run the extraction process on all syllabus PDF files.
        Override the parent class run method.
        
        Returns:
            tuple: (success_count, fail_count, skipped_count)
        """
        print(f"Starting Mathpix PDF extraction for syllabus files in: {self.input_dir}")
        print(f"Results will be saved to: {self.syllabus_output_dir}")
        
        # Ensure the syllabus output directory exists
        os.makedirs(self.syllabus_output_dir, exist_ok=True)
        
        # Get list of syllabus PDF files
        pdf_files = await self.get_syllabus_files()
        
        if not pdf_files:
            print(f"No syllabus PDF files found in {self.input_dir}")
            return 0, 0, 0
        
        print(f"Found {len(pdf_files)} syllabus PDF files to process")
        
        # Process each syllabus PDF
        success_count = 0
        fail_count = 0
        skipped_count = 0
        
        for file_path in pdf_files:
            # Check if this file has already been processed with results
            relative_path = os.path.relpath(file_path, self.input_dir)
            syllabus_key = f"syllabus:{relative_path}"
            syllabus_output_dir = os.path.join(self.syllabus_output_dir, Path(file_path).stem)
            
            if (syllabus_key in self.processed_files and 
                os.path.exists(syllabus_output_dir) and 
                os.path.exists(os.path.join(syllabus_output_dir, f"{Path(file_path).stem}.md"))):
                print(f"Skipping already processed syllabus file: {file_path}")
                skipped_count += 1
                continue
            
            success = await self.process_syllabus(file_path)
            if success:
                success_count += 1
            else:
                fail_count += 1
        
        print(f"\nSyllabus extraction complete. Results: {success_count} successful, {fail_count} failed, {skipped_count} skipped")
        return success_count, fail_count, skipped_count


async def main():
    """Example usage of the SyllabusExtractor class."""
    extractor = SyllabusExtractor()
    await extractor.run()


if __name__ == "__main__":
    asyncio.run(main())