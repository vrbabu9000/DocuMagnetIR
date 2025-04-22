import httpx
import asyncio
import json
import os
import time
import traceback
from pathlib import Path
from dotenv import load_dotenv



# Load environment variables from .env file
env_path = ".env"
load_dotenv(dotenv_path=env_path)

# Get API credentials
app_id = os.environ.get("MATHPIX_APP_ID")
app_key = os.environ.get("MATHPIX_APP_KEY")

BASE_URL = "https://api.mathpix.com/v3/pdf"
APP_KEY = app_key  # Replace with your actual app key
MAX_RETRIES = 5
RETRY_DELAY = 5  # seconds

async def upload_pdf_file(file_path):
    """
    Uploads a PDF file from the local filesystem for processing and retrieves the `pdf_id`.
    """
    print(f"Uploading PDF: {file_path}")
    
    headers = {"app_key": APP_KEY}
    
    # For file uploads, we need to use multipart/form-data
    files = {"file": open(file_path, "rb")}
    
    # Add streaming parameter
    data = {"options_json": json.dumps({"streaming": True})}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                BASE_URL, 
                headers=headers, 
                files=files, 
                data=data
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"PDF uploaded successfully with ID: {data.get('pdf_id')}")
                print(data)
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

async def check_processing_status(pdf_id):
    """
    Checks the processing status of a PDF.
    """
    url = f"{BASE_URL}/{pdf_id}"
    headers = {"app_key": APP_KEY}
    
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

async def wait_for_processing(pdf_id, max_attempts=12, delay=5):
    """
    Waits for the PDF processing to complete by polling the status.
    Returns True if processing completed, False if timed out.
    """
    print("Checking processing status...")
    
    for attempt in range(1, max_attempts + 1):
        print(f"Attempt {attempt}/{max_attempts}: ", end="")
        
        status_data = await check_processing_status(pdf_id)
        
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

async def stream_pdf(pdf_id):
    """
    Streams the processed PDF data using the `pdf_id`.
    """
    url = f"{BASE_URL}/{pdf_id}/stream"
    headers = {"app_key": APP_KEY}
    
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

async def save_results(results, output_file):
    """
    Saves the results to a file.
    """
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {output_file}")
        return True
    except Exception as e:
        print(f"Error saving results: {e}")
        print(traceback.format_exc())
        return False

async def process_pdf(file_path, output_dir="results"):
    """
    Main function to process a PDF file with streaming.
    """
    print("Starting Mathpix PDF processing with streaming enabled...")
    
    # 1. Upload the PDF
    pdf_id = await upload_pdf_file(file_path)
    if not pdf_id:
        return False
    
    # 2. Stream the results (no need to wait for processing completion)
    results = await stream_pdf(pdf_id)
    
    if not results:
        print("No results were streamed. Trying to check status...")
        # If streaming didn't work, fall back to waiting for processing
        processing_completed = await wait_for_processing(pdf_id)
        if not processing_completed:
            print("PDF processing failed")
            return False
    
    # 3. Save the results
    file_name = Path(file_path).stem
    output_file = os.path.join(output_dir, f"{file_name}_results.json")
    success = await save_results(results, output_file)
    
    return success

async def main():
    # Replace with your PDF file path
    pdf_path = r"d:\MSE_DS_JHU\Semester1\Information_Retrieval_Web_Agents\Git\DocuMagnetIR\data\sample_papers\ps1_updated.pdf"
    
    success = await process_pdf(pdf_path)
    if success:
        print("PDF processing completed successfully")
    else:
        print("PDF processing failed")

if __name__ == "__main__":
    asyncio.run(main())