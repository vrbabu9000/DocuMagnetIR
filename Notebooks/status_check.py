import httpx
import asyncio
import json
import os
import argparse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API credentials
app_key = os.environ.get("MATHPIX_APP_KEY")
if not app_key:
    raise ValueError("MATHPIX_APP_KEY not found in environment variables")

BASE_URL = "https://api.mathpix.com/v3/pdf"

async def check_processing_status(pdf_id):
    """
    Checks the processing status of a PDF given its ID.
    """
    url = f"{BASE_URL}/{pdf_id}"
    headers = {"app_key": app_key}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                status_data = response.json()
                print(f"Status for PDF ID {pdf_id}:")
                print(f"- Status: {status_data.get('status')}")
                print(f"- Progress: {status_data.get('progress', 'N/A')}")
                if status_data.get('error'):
                    print(f"- Error: {status_data.get('error')}")
                
                # Print available conversion formats if completed
                if status_data.get('status') == 'completed':
                    print("\nAvailable conversion formats:")
                    for format_type in status_data.get('conversion_formats', {}):
                        print(f"- {format_type}")
                
                # Pretty print the full response for detailed inspection
                print("\nFull response:")
                print(json.dumps(status_data, indent=2))
                
                return status_data
            else:
                print(f"Failed to check status: {response.status_code}")
                print(response.text)
                return None
    except Exception as e:
        print(f"Error checking status: {e}")
        return None

async def main():
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description="Check Mathpix PDF processing status")
    parser.add_argument("pdf_id", help="The PDF ID to check status for")
    args = parser.parse_args()
    
    # Get the PDF ID from command line arguments
    pdf_id = args.pdf_id
    
    # Check the status
    await check_processing_status(pdf_id)

if __name__ == "__main__":
    asyncio.run(main())