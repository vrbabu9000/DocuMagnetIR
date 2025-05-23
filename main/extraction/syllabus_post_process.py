import os
import json
import glob
import asyncio
import time
from pathlib import Path
import anthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
import streamlit as st


class SyllabusPostProcessor:
    def __init__(self, root_dir=None, api_key=None, model="claude-3-5-haiku-20241022"):
        """
        Initialize the post-processor for processing syllabus markdown files with Claude API.
        
        Args:
            root_dir (str): The root directory of the project
            api_key (str): API key for Anthropic
            model (str): Claude model to use for processing
        """
        self.root_dir = root_dir if root_dir else self._get_project_root()
        self.api_key = st.secrets["ANTHROPIC_API_KEY"]
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
        return current_file.parent.parent.parent  # Go up one level to reach project root
    
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
            # Check if the file has already been processed
            file_base_name = os.path.basename(file_path).replace('.md', '')
            output_file = os.path.join(self.syllabus_results_dir, syllabus_name, f"{file_base_name}_analyzed.json")
            
            if os.path.exists(output_file):
                print(f"Skipping {file_path} - analyzed JSON already exists at {output_file}")
                return (True, file_path, None)
            
            # Read the content of the markdown file
            with open(file_path, 'r', encoding='utf-8') as file:
                syllabus_text = file.read()
            
            # Prepare the prompt
            prompt = self._prepare_prompt(syllabus_text)
            
            print(f"Processing file: {file_path}")
            
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
            
            # Save the result to a JSON file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2)
            
            print(f"Successfully processed: {file_path}")
            print(f"Result saved to: {output_file}")
            
            return (True, file_path, result)
        except Exception as e:
            print(f"Error processing file {file_path}: {str(e)}")
            return (False, file_path, None)
    
    async def run(self):
        """
        Run the post-processing pipeline on all markdown files in the syllabus_extract_ocr directory,
        processing one file at a time (no batching).
        
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
        
        # Process each syllabus folder
        for syllabus_folder in syllabus_folders:
            folder_path = os.path.join(self.syllabus_results_dir, syllabus_folder)
            md_files = glob.glob(os.path.join(folder_path, "*.md"))
            
            print(f"\nProcessing folder: {syllabus_folder}")
            print(f"Found {len(md_files)} markdown files")
            
            # Process each file individually
            for file_path in md_files:
                # Process the file
                success, _, result = await self._process_file(file_path, syllabus_folder)
                
                if result is None and success:
                    # File was skipped because it was already processed
                    skipped_count += 1
                elif success:
                    success_count += 1
                else:
                    failure_count += 1
        
        return success_count, failure_count, skipped_count

async def main():
    """Main function to run the post-processor."""
    processor = SyllabusPostProcessor()
    success, failed, skipped = await processor.run()
    print(f"\nSyllabus post-processing completed: {success} successful, {failed} failed, {skipped} skipped")

if __name__ == "__main__":
    asyncio.run(main())