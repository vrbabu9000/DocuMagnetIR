import os
import json
import glob
import asyncio
import time
from pathlib import Path
import anthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request


class SyllabusPostProcessor:
    def __init__(self, root_dir=None, api_key=None, batch_size=20, model="claude-3-5-haiku-20241022"):
        """
        Initialize the post-processor for processing syllabus markdown files with Claude API.
        
        Args:
            root_dir (str): The root directory of the project
            api_key (str): API key for Anthropic
            batch_size (int): Maximum number of requests to process in a batch
            model (str): Claude model to use for processing
        """
        self.root_dir = root_dir if root_dir else self._get_project_root()
        self.api_key = api_key if api_key else os.environ.get("ANTHROPIC_API_KEY")
        self.batch_size = batch_size
        self.model = model
        
        # Initialize the Claude client
        self.client = anthropic.Anthropic(api_key=self.api_key)
        
        # Set up directories
        self.syllabus_results_dir = os.path.join(self.root_dir, "data", "syllabus_extract_ocr")
        self.prompt_path = os.path.join(self.root_dir, "prompts", "syllabus.txt")
        
        # Load the prompt template
        self.prompt_template = self._load_prompt_template()
        
    def _get_project_root(self):
        """Determine the project root based on the current file location."""
        current_file = Path(__file__)
        return current_file.parent.parent  # Go up one level to reach project root
    
    def _load_prompt_template(self):
        """Load the prompt template from the specified file."""
        try:
            with open(self.prompt_path, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            print(f"Error: Prompt file not found at {self.prompt_path}")
            return None
        
    def _prepare_prompt(self, syllabus_text):
        """Prepare the prompt by replacing the placeholder with the actual text."""
        if not self.prompt_template:
            raise ValueError("Prompt template is not loaded")
        
        return self.prompt_template.replace("{{syllabus_text}}", syllabus_text)
    
    def _extract_text_from_content(self, content):
        """
        Extract text from Claude's content response, which could be a string or a list of content blocks.
        
        Args:
            content: Claude's response content (string or list)
            
        Returns:
            str: Extracted text content
        """
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            # Concatenate all text blocks in the content list
            text_parts = []
            for item in content:
                if hasattr(item, 'text'):  # Handle TextBlock objects
                    text_parts.append(item.text)
                elif isinstance(item, dict) and 'type' in item and item['type'] == 'text':
                    text_parts.append(item.get('text', ''))
                elif isinstance(item, str):
                    text_parts.append(item)
            return ' '.join(text_parts)
        else:
            # Try to extract text if it has a 'text' attribute
            if hasattr(content, 'text'):
                return content.text
            raise ValueError(f"Unexpected content format: {type(content)}")
    
    def _parse_claude_response(self, response):
        """
        Parse Claude's response into a structured dictionary.
        
        Args:
            response (str): Claude's response text
            
        Returns:
            dict: Structured dictionary with syllabus information
        """
        try:
            # Try to parse the response as JSON directly
            result = json.loads(response)
            return result
        except json.JSONDecodeError:
            # If direct parsing fails, attempt to extract JSON from the response
            # Look for a JSON structure between triple backticks or code block markers
            import re
            json_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
            match = re.search(json_pattern, response)
            
            if match:
                try:
                    result = json.loads(match.group(1))
                    return result
                except json.JSONDecodeError:
                    print("Error parsing JSON from code block")
            
            # Fallback parsing logic for non-JSON responses
            # This can be customized based on the expected response format
            print("Warning: Could not parse Claude's response as JSON, returning raw response")
            return {"raw_response": response}
    
    async def _process_file(self, file_path, syllabus_name):
        """
        Process a single markdown file with Claude API.
        
        Args:
            file_path (str): Path to the markdown file
            syllabus_name (str): Name of the syllabus folder
            
        Returns:
            tuple: (Success status, file path, result dictionary)
        """
        try:
            # Read the content of the markdown file
            with open(file_path, 'r', encoding='utf-8') as file:
                syllabus_text = file.read()
            
            # Prepare the prompt
            prompt = self._prepare_prompt(syllabus_text)
            
            # Send to Claude API
            message = self.client.messages.create(
                model=self.model,
                max_tokens=8192,
                temperature=0.2,  # Lower temperature for more consistent parsing
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Extract text content and parse the response
            content_text = self._extract_text_from_content(message.content)
            result = self._parse_claude_response(content_text)
            
            return (True, file_path, result)
        except Exception as e:
            print(f"Error processing file {file_path}: {str(e)}")
            return (False, file_path, None)
    
    async def _process_batch(self, batch_files):
        """
        Process a batch of markdown files using Claude's batch API.
        
        Args:
            batch_files (list): List of tuples containing (file_path, syllabus_name)
            
        Returns:
            list: List of tuples with (success, file_path, result)
        """
        # Create file_path map using custom_id as key
        file_path_map = {}
        batch_requests = []
        
        # Prepare batch requests
        for idx, (file_path, syllabus_name) in enumerate(batch_files):
            try:
                # Create a unique custom_id for this file
                custom_id = f"file_{idx}"
                file_path_map[custom_id] = (file_path, syllabus_name)
                
                # Read the content of the markdown file
                with open(file_path, 'r', encoding='utf-8') as file:
                    syllabus_text = file.read()
                
                # Prepare the prompt
                prompt = self._prepare_prompt(syllabus_text)
                
                # Add to batch requests using the proper Request structure
                batch_requests.append(
                    Request(
                        custom_id=custom_id,
                        params=MessageCreateParamsNonStreaming(
                            model=self.model,
                            max_tokens=8192,
                            temperature=0.2,  # Lower temperature for more consistent parsing
                            messages=[
                                {
                                    "role": "user",
                                    "content": prompt
                                }
                            ]
                        )
                    )
                )
            except Exception as e:
                print(f"Error preparing batch request for {file_path}: {str(e)}")
        
        # Process the batch
        try:
            print(f"Creating batch with {len(batch_requests)} requests...")
            # Create the batch and get the batch ID
            batch_response = self.client.messages.batches.create(requests=batch_requests)
            batch_id = batch_response.id
            
            print(f"Batch created with ID: {batch_id}")
            print(f"Initial status: {batch_response.processing_status}")
            
            # Poll until the batch is complete (ended status)
            max_polls = 60  # Maximum number of polling attempts
            poll_interval = 10  # Seconds between polls
            
            for i in range(max_polls):
                # Get the current batch status
                batch_status = self.client.messages.batches.retrieve(batch_id)
                
                print(f"Polling batch status ({i+1}/{max_polls}): {batch_status.processing_status}")
                print(f"Counts: {batch_status.request_counts}")
                
                # Check if processing has ended
                if batch_status.processing_status == "ended":
                    break
                
                # Wait before polling again
                await asyncio.sleep(poll_interval)
            
            # Check if the batch completed successfully
            if batch_status.processing_status != "ended":
                print(f"Batch processing did not complete within expected time. Last status: {batch_status.processing_status}")
                raise TimeoutError("Batch processing timed out")
            
            # Process the results
            results = []
            print("Processing batch results...")
            
            # Stream the results from the batch
            for result in self.client.messages.batches.results(batch_id):
                custom_id = result.custom_id
                file_path, syllabus_name = file_path_map.get(custom_id, (None, None))
                
                if file_path is None:
                    print(f"Warning: Could not find file path for custom_id {custom_id}")
                    continue
                
                if result.result.type == "succeeded":
                    try:
                        # Extract text content from the message
                        message = result.result.message
                        content_text = self._extract_text_from_content(message.content)
                        parsed_result = self._parse_claude_response(content_text)
                        results.append((True, file_path, parsed_result))
                        print(f"Successfully processed: {file_path}")
                    except Exception as e:
                        print(f"Error parsing result for {file_path}: {str(e)}")
                        results.append((False, file_path, None))
                else:
                    # Handle error cases
                    error_type = result.result.type
                    error_message = ""
                    if error_type == "errored" and hasattr(result.result, "error"):
                        error_message = result.result.error.message if hasattr(result.result.error, "message") else str(result.result.error)
                    
                    print(f"Failed to process {file_path}: {error_type} - {error_message}")
                    results.append((False, file_path, None))
            
            return results
        except Exception as e:
            print(f"Error processing batch: {str(e)}")
            # Fall back to individual processing if batch fails
            print("Falling back to individual processing...")
            results = []
            for file_path, syllabus_name in batch_files:
                result = await self._process_file(file_path, syllabus_name)
                results.append(result)
            return results
    
    async def run(self):
        """
        Run the post-processing pipeline on all markdown files in the syllabus_extract_ocr directory.
        
        Returns:
            tuple: (success count, failure count, skipped count)
        """
        success_count = 0
        failure_count = 0
        skipped_count = 0
        
        # Get all syllabus folders in the syllabus_extract_ocr directory
        if not os.path.exists(self.syllabus_results_dir):
            print(f"Syllabus results directory not found: {self.syllabus_results_dir}")
            return 0, 0, 0
        
        syllabus_folders = [f for f in os.listdir(self.syllabus_results_dir) 
                           if os.path.isdir(os.path.join(self.syllabus_results_dir, f))]
        
        if not syllabus_folders:
            print(f"No syllabus folders found in {self.syllabus_results_dir}")
            return 0, 0, 0
        
        print(f"Found {len(syllabus_folders)} syllabus folders to process")
        
        # Prepare a list of all markdown files to process
        all_files = []
        for syllabus_folder in syllabus_folders:
            folder_path = os.path.join(self.syllabus_results_dir, syllabus_folder)
            md_files = glob.glob(os.path.join(folder_path, "*.md"))
            
            for file_path in md_files:
                # Check if processed JSON already exists for this file
                file_base_name = os.path.basename(file_path).replace('.md', '')
                json_path = os.path.join(folder_path, f"{file_base_name}_analyzed.json")
                
                if os.path.exists(json_path):
                    print(f"Skipping {file_path} - analyzed JSON already exists")
                    skipped_count += 1
                    continue
                
                all_files.append((file_path, syllabus_folder))
        
        print(f"Found {len(all_files)} files to process, {skipped_count} files skipped")
        
        # Process files in batches
        for i in range(0, len(all_files), self.batch_size):
            batch = all_files[i:i + self.batch_size]
            batch_results = await self._process_batch(batch)
            
            # Save results and update counts
            for success, file_path, result in batch_results:
                if success and result:
                    # Get the syllabus name from the file path
                    syllabus_name = os.path.basename(os.path.dirname(file_path))
                    
                    # Get the base name of the markdown file (without extension)
                    file_base_name = os.path.basename(file_path).replace('.md', '')
                    
                    # Create output file path
                    output_file = os.path.join(self.syllabus_results_dir, syllabus_name, f"{file_base_name}_analyzed.json")
                    
                    # Save the result as JSON
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(result, f, indent=2)
                    
                    success_count += 1
                else:
                    failure_count += 1
        
        return success_count, failure_count, skipped_count

async def main():
    """Main function to run the post-processor."""
    processor = SyllabusPostProcessor()
    success, failed, skipped = await processor.run()
    print(f"Syllabus post-processing completed: {success} successful, {failed} failed, {skipped} skipped")

if __name__ == "__main__":
    asyncio.run(main())