import httpx
import asyncio
import json
import os
import time
import traceback
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st


class MathpixExtractor:
    """
    A class to handle the extraction of text and math from PDFs using Mathpix API.
    Processes all PDFs in a specified directory and keeps track of already processed files.
    """

    def __init__(self, input_dir="DocuMagnetIR/data/sample_papers", output_dir="DocuMagnetIR/data/ocr_results"):
        """
        Initialize the MathpixExtractor with input and output directories.
        
        Args:
            input_dir (str): Directory containing PDFs to process
            output_dir (str): Directory to save extraction results
        """
        # Load environment variables from .env file
        env_path = ".env"
        load_dotenv(dotenv_path=env_path)
        
        # Get API credentials
        self.app_id = st.secrets["MATHPIX_APP_ID"]
        self.app_key = st.secrets["MATHPIX_APP_ID"]
        
        if not self.app_key:
            raise ValueError("MATHPIX_APP_KEY environment variable not found")
        
        self.BASE_URL = "https://api.mathpix.com/v3/pdf"
        self.MAX_RETRIES = 5
        self.RETRY_DELAY = 5  # seconds
        
        # Set up directories
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.processed_file_map = os.path.join(output_dir, "processed_files.json")
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Set up API options
        self.options = {
            # Core parameters
            "streaming": True,  # Enable streaming for the request
            "include_equation_tags": True,  # Include equation number tags
            "include_smiles": True,  # Enable chemistry diagram OCR
            "include_chemistry_as_image": True,  # Return image crop with SMILES in alt-text
            "include_diagram_text": True,  # Enable text extraction from diagrams
            "numbers_default_to_math": True,  # Numbers are always treated as math
            
            # Delimiter settings
            "math_inline_delimiters": ["$", "$"],  # Inline math delimiters
            "math_display_delimiters": ["$$", "$$"],  # Display math delimiters
            
            # Page settings
            "page_ranges": "1-",  # Process all pages
            
            # Processing options
            "enable_spell_check": True,  # Enable predictive mode for English handwriting
            "auto_number_sections": True,  # Automatically number sections
            "remove_section_numbering": False,  # Don't remove existing section numbering
            "preserve_section_numbering": False,  # Keep existing section numbering
            "enable_tables_fallback": True,  # Enable advanced table processing
            "fullwidth_punctuation": False,  # Use halfwidth Unicode for punctuation
            
            # Conversion formats
            "conversion_formats": {
                "md": True,  # Markdown
            }
        }
        
        # Load or initialize processed files map
        self.processed_files = self._load_processed_files()

    def _load_processed_files(self):
        """
        Load the map of processed files from JSON, or create an empty map if not found.
        
        Returns:
            dict: Map of filenames to pdf_ids for processed files
        """
        if os.path.exists(self.processed_file_map):
            try:
                with open(self.processed_file_map, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Error reading processed files map. Creating a new one.")
                return {}
        return {}

    def _save_processed_files(self):
        """Save the current map of processed files to JSON."""
        with open(self.processed_file_map, 'w') as f:
            json.dump(self.processed_files, f, indent=2)

    async def upload_pdf_file(self, file_path):
        """
        Uploads a PDF file from the local filesystem for processing and retrieves the `pdf_id`.
        
        Args:
            file_path (str): Path to the PDF file
            
        Returns:
            str or None: pdf_id if successful, None otherwise
        """
        print(f"Uploading PDF: {file_path}")
        
        headers = {"app_key": self.app_key}
        
        # For file uploads, we need to use multipart/form-data
        files = {"file": open(file_path, "rb")}
        
        # Add streaming parameter
        data = {"options_json": json.dumps(self.options)}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.BASE_URL, 
                    headers=headers, 
                    files=files, 
                    data=data
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"PDF uploaded successfully with ID: {data.get('pdf_id')}")
                    return data.get("pdf_id")
                else:
                    print(f"Failed to upload PDF: {response.status_code}, {response.text}")
                    return None
        except Exception as e:
            print(f"Error uploading PDF: {e}")
            print(traceback.format_exc())
            return None
        finally:
            # Make sure to close the file
            if 'files' in locals() and 'file' in files:
                files['file'].close()

    async def check_processing_status(self, pdf_id):
        """
        Checks the processing status of a PDF.
        
        Args:
            pdf_id (str): The ID of the PDF to check
            
        Returns:
            dict or None: Status information if successful, None otherwise
        """
        url = f"{self.BASE_URL}/{pdf_id}"
        headers = {"app_key": self.app_key}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"Failed to check status: {response.status_code}, {response.text}")
                    return None
        except Exception as e:
            print(f"Error checking status: {e}")
            return None

    async def wait_for_processing(self, pdf_id, max_attempts=12, delay=5):
        """
        Waits for the PDF processing to complete by polling the status.
        
        Args:
            pdf_id (str): The ID of the PDF being processed
            max_attempts (int): Maximum number of status check attempts
            delay (int): Seconds to wait between attempts
            
        Returns:
            bool: True if processing completed, False if timed out or failed
        """
        print("Checking processing status...")
        
        for attempt in range(1, max_attempts + 1):
            print(f"Attempt {attempt}/{max_attempts}: ", end="")
            
            status_data = await self.check_processing_status(pdf_id)
            
            if not status_data:
                print("Failed to get status")
                await asyncio.sleep(delay)
                continue
            
            status = status_data.get("status")
            print(f"Status = {status}")
            
            if status == "completed":
                print("Processing completed successfully!")
                return True
            elif status in ["error", "failed"]:
                print(f"Processing failed with status: {status}")
                if "error" in status_data:
                    print(f"Error details: {status_data['error']}")
                return False
            else:
                print(f"Processing in progress ({status})... waiting {delay} seconds")
                await asyncio.sleep(delay)
        
        print("Timed out waiting for processing to complete")
        return False

    async def stream_pdf(self, pdf_id):
        """
        Streams the processed PDF data using the `pdf_id`.
        
        Args:
            pdf_id (str): The ID of the PDF to stream
            
        Returns:
            list: List of JSON chunks from the stream
        """
        url = f"{self.BASE_URL}/{pdf_id}/stream"
        headers = {"app_key": self.app_key}
        
        print(f"Starting streaming for PDF ID: {pdf_id}")
        results = []
        
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(timeout=None)) as client:
                async with client.stream("GET", url, headers=headers) as response:
                    if response.status_code == 200:
                        print("Connected to the stream!")
                        async for line in response.aiter_lines():
                            if line.strip():  # Ignore empty lines
                                try:
                                    data = json.loads(line)
                                    # Store the complete result
                                    results.append(data)
                                    
                                    # Print a preview (only first 50 chars of text if available)
                                    preview = data.copy()
                                    if 'text' in preview and isinstance(preview['text'], str) and len(preview['text']) > 50:
                                        preview['text'] = preview['text'][:50] + "..."
                                    print(f"Received chunk: {preview}")
                                except json.JSONDecodeError:
                                    print(f"Failed to decode line: {line}")
                    else:
                        print(f"Failed to connect to stream: {response.status_code}, {response.text}")
            
            return results
        except Exception as e:
            print(f"Streaming error: {e}")
            print(traceback.format_exc())
            return []

    async def save_results(self, results, output_dir, file_name):
        """
        Saves the results to files and extracts MMD content.
        
        Args:
            results (list): List of JSON chunks from streaming
            output_dir (str): Directory to save results
            file_name (str): Base name for output files
            
        Returns:
            bool: True if saving was successful, False otherwise
        """
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # Save the JSON results for reference
            json_file = os.path.join(output_dir, f"{file_name}_results.json")
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)
            print(f"Results saved to {json_file}")
            
            # Extract text content from streaming results and save as MMD
            mmd_content = ""
            for chunk in results:
                if 'text' in chunk:
                    mmd_content += chunk['text']
            
            # Save MMD content
            mmd_file = os.path.join(output_dir, f"{file_name}.mmd")
            with open(mmd_file, 'w', encoding='utf-8') as f:
                f.write(mmd_content)
            print(f"MMD content extracted and saved to {mmd_file}")
            
            return True
        except Exception as e:
            print(f"Error saving results: {e}")
            print(traceback.format_exc())
            return False

    async def download_conversion_formats(self, pdf_id, output_dir, file_name):
        """
        Downloads available conversion formats directly from Mathpix API endpoints.
        
        Args:
            pdf_id (str): The ID of the processed PDF
            output_dir (str): Directory to save downloaded formats
            file_name (str): Base name for output files
            
        Returns:
            bool: True if any formats were downloaded successfully
        """
        print(f"Waiting for processing to complete before downloading formats...")
        
        # Wait for processing to complete
        processing_complete = await self.wait_for_processing(pdf_id)
        if not processing_complete:
            print("Processing did not complete. Some formats may not be available.")
        
        print(f"Downloading conversion formats for PDF ID: {pdf_id}")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Define formats to download
        formats = [
            {"ext": "mmd", "binary": False},
            {"ext": "md", "binary": False},
            {"ext": "lines.mmd.json", "binary": False}
        ]
        
        success = False
        
        for format_info in formats:
            ext = format_info["ext"]
            is_binary = format_info["binary"]
            
            url = f"{self.BASE_URL}/{pdf_id}.{ext}"
            headers = {"app_key": self.app_key}
            
            print(f"Requesting {ext} format...")
            
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, headers=headers)
                    
                    if response.status_code == 200:
                        # Determine the output filename
                        output_filename = f"{file_name}.{ext}"
                        if ext == "tex":
                            output_filename = f"{file_name}.tex.zip"
                        
                        output_path = os.path.join(output_dir, output_filename)
                        
                        # Save the content
                        if is_binary:
                            with open(output_path, "wb") as f:
                                f.write(response.content)
                        else:
                            with open(output_path, "w", encoding="utf-8") as f:
                                f.write(response.text)
                        
                        print(f"Downloaded {ext} format to {output_path}")
                        success = True
                    else:
                        print(f"Failed to download {ext} format: {response.status_code}, {response.text}")
                
            except Exception as e:
                print(f"Error downloading {ext} format: {e}")
                print(traceback.format_exc())
        
        return success

    async def process_pdf(self, file_path):
        """
        Process a single PDF file with Mathpix.
        
        Args:
            file_path (str): Path to the PDF file
            
        Returns:
            bool: True if processing was successful, False otherwise
        """
        print(f"\n{'='*80}\nProcessing PDF: {file_path}\n{'='*80}")
        
        file_name = Path(file_path).stem
        
        # Create a dedicated output directory for this PDF
        pdf_output_dir = os.path.join(self.output_dir, file_name)
        os.makedirs(pdf_output_dir, exist_ok=True)
        
        # Check if this file has already been processed
        relative_path = os.path.relpath(file_path, self.input_dir)
        if relative_path in self.processed_files:
            pdf_id = self.processed_files[relative_path]
            print(f"PDF {file_path} was already processed with ID: {pdf_id}")
            
            # Check if results exist
            if os.path.exists(os.path.join(pdf_output_dir, f"{file_name}.md")):
                print("Results already exist. Skipping processing.")
                return True
            else:
                print("Results not found. Re-downloading conversion formats...")
                await self.download_conversion_formats(pdf_id, pdf_output_dir, file_name)
                return True
        
        # 1. Upload the PDF
        pdf_id = await self.upload_pdf_file(file_path)
        if not pdf_id:
            return False
        
        # 2. Stream the results
        results = await self.stream_pdf(pdf_id)
        
        # 3. Save the streamed results and extract MMD
        success = await self.save_results(results, pdf_output_dir, file_name)
        
        # 4. Download additional formats after processing is complete
        await self.download_conversion_formats(pdf_id, pdf_output_dir, file_name)
        
        # 5. Update the processed files map
        if success:
            self.processed_files[relative_path] = pdf_id
            self._save_processed_files()
        
        return success

    async def get_pdf_files(self):
        """
        Get a list of PDF files in the input directory.
        
        Returns:
            list: List of paths to PDF files
        """
        pdf_files = []
        for root, _, files in os.walk(self.input_dir):
            for file in files:
                if file.lower().endswith('.pdf'):
                    pdf_files.append(os.path.join(root, file))
        return pdf_files

    async def run(self):
        """
        Run the extraction process on all PDF files in the input directory.
        
        Returns:
            tuple: (success_count, fail_count, skipped_count)
        """
        print(f"Starting Mathpix PDF extraction for files in: {self.input_dir}")
        print(f"Results will be saved to: {self.output_dir}")
        
        # Get list of PDF files
        pdf_files = await self.get_pdf_files()
        
        if not pdf_files:
            print(f"No PDF files found in {self.input_dir}")
            return 0, 0, 0
        
        print(f"Found {len(pdf_files)} PDF files to process")
        
        # Process each PDF
        success_count = 0
        fail_count = 0
        skipped_count = 0
        
        for file_path in pdf_files:
            # Check if this file has already been processed with results
            relative_path = os.path.relpath(file_path, self.input_dir)
            pdf_output_dir = os.path.join(self.output_dir, Path(file_path).stem)
            
            if (relative_path in self.processed_files and 
                os.path.exists(pdf_output_dir) and 
                len(os.listdir(pdf_output_dir)) > 0):
                print(f"Skipping already processed file: {file_path}")
                skipped_count += 1
                continue
            
            success = await self.process_pdf(file_path)
            if success:
                success_count += 1
            else:
                fail_count += 1
        
        print(f"\nExtraction complete. Results: {success_count} successful, {fail_count} failed, {skipped_count} skipped")
        return success_count, fail_count, skipped_count


async def main():
    """Example usage of the MathpixExtractor class."""
    extractor = MathpixExtractor()
    await extractor.run()


if __name__ == "__main__":
    asyncio.run(main())