import httpx
import asyncio
import json
import os
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API credentials
app_key = os.environ.get("MATHPIX_APP_KEY")
if not app_key:
    raise ValueError("MATHPIX_APP_KEY not found in environment variables")

BASE_URL = "https://api.mathpix.com/v3/pdf"

async def download_formats(pdf_id, output_dir, formats=None):
    """
    Downloads available formats for a PDF given its ID.
    """
    # Default formats to download if none specified
    if formats is None:
        formats = [
            {"ext": "mmd", "binary": False},
            {"ext": "md", "binary": False},
            {"ext": "tex", "binary": True},
            {"ext": "html", "binary": False},
            {"ext": "lines.json", "binary": False},
            {"ext": "lines.mmd.json", "binary": False}
        ]
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Download each format
    successful_downloads = 0
    total_formats = len(formats)
    
    for format_info in formats:
        ext = format_info["ext"]
        is_binary = format_info["binary"]
        
        url = f"{BASE_URL}/{pdf_id}.{ext}"
        headers = {"app_key": app_key}
        
        print(f"Requesting {ext} format...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    # Determine the output filename
                    output_filename = f"{pdf_id}.{ext}"
                    if ext == "tex":
                        output_filename = f"{pdf_id}.tex.zip"
                    
                    output_path = os.path.join(output_dir, output_filename)
                    
                    # Save the content
                    if is_binary:
                        with open(output_path, "wb") as f:
                            f.write(response.content)
                    else:
                        with open(output_path, "w", encoding="utf-8") as f:
                            f.write(response.text)
                    
                    print(f"✓ Downloaded {ext} format to {output_path}")
                    successful_downloads += 1
                else:
                    print(f"✗ Failed to download {ext} format: {response.status_code}")
                    print(response.text)
            
        except Exception as e:
            print(f"✗ Error downloading {ext} format: {e}")
    
    print(f"\nDownload summary: {successful_downloads}/{total_formats} formats downloaded successfully")
    return successful_downloads > 0

async def check_processing_status(pdf_id):
    """
    Checks if processing is complete for the PDF.
    """
    url = f"{BASE_URL}/{pdf_id}"
    headers = {"app_key": app_key}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                status_data = response.json()
                status = status_data.get("status")
                print(f"PDF processing status: {status}")
                return status == "completed"
            else:
                print(f"Failed to check status: {response.status_code}")
                return False
    except Exception as e:
        print(f"Error checking status: {e}")
        return False

async def download_stream_results(pdf_id, output_dir):
    """
    Downloads streaming results for a PDF.
    """
    url = f"{BASE_URL}/{pdf_id}/stream"
    headers = {"app_key": app_key}
    
    print(f"Downloading streaming results for PDF ID: {pdf_id}")
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
                                results.append(data)
                                print(".", end="", flush=True)  # Progress indicator
                            except json.JSONDecodeError:
                                print(f"Failed to decode line: {line}")
                    print("\nStream download complete!")
                else:
                    print(f"Failed to connect to stream: {response.status_code}")
                    return False
        
        # Save the results
        if results:
            # Save JSON
            json_path = os.path.join(output_dir, f"{pdf_id}_results.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)
            print(f"Saved streaming results to {json_path}")
            
            # Extract and save MMD content
            mmd_content = ""
            for chunk in results:
                if 'text' in chunk:
                    mmd_content += chunk['text']
            
            if mmd_content:
                mmd_path = os.path.join(output_dir, f"{pdf_id}_stream.mmd")
                with open(mmd_path, 'w', encoding='utf-8') as f:
                    f.write(mmd_content)
                print(f"Saved extracted MMD content to {mmd_path}")
            
            return True
        else:
            print("No streaming results found")
            return False
    except Exception as e:
        print(f"Streaming error: {e}")
        return False

async def main():
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description="Download Mathpix PDF processing results")
    parser.add_argument("pdf_id", help="The PDF ID to download results for")
    parser.add_argument("--output-dir", "-o", default="results", help="Directory to save results (default: 'results')")
    parser.add_argument("--wait", "-w", action="store_true", help="Wait for processing to complete if not already done")
    parser.add_argument("--stream", "-s", action="store_true", help="Download streaming results")
    args = parser.parse_args()
    
    # Create specific output directory for this PDF ID
    output_dir = os.path.join(args.output_dir, args.pdf_id)
    os.makedirs(output_dir, exist_ok=True)
    
    # Check if processing is complete
    is_complete = await check_processing_status(args.pdf_id)
    
    # Wait for processing if requested and not complete
    if args.wait and not is_complete:
        print("Waiting for processing to complete...")
        max_attempts = 12
        delay = 5  # seconds
        
        for attempt in range(1, max_attempts + 1):
            print(f"Attempt {attempt}/{max_attempts}... ", end="")
            is_complete = await check_processing_status(args.pdf_id)
            
            if is_complete:
                print("Processing completed!")
                break
            else:
                print(f"Still processing. Waiting {delay} seconds...")
                await asyncio.sleep(delay)
        
        if not is_complete:
            print("Timed out waiting for processing to complete.")
            print("Will try to download available formats anyway.")
    
    # Download results
    if args.stream:
        await download_stream_results(args.pdf_id, output_dir)
    
    # Always attempt to download the format files
    await download_formats(args.pdf_id, output_dir)
    
    print(f"\nAll available results downloaded to {output_dir}")

if __name__ == "__main__":
    asyncio.run(main())