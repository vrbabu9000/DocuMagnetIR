import os
import json
import asyncio
from pathlib import Path
import anthropic


class BatchRetriever:
    def __init__(self, batch_id, api_key=None, ocr_results_dir=None):
        """
        Initialize a batch retriever for a specific batch ID.
        
        Args:
            batch_id (str): The ID of the batch to retrieve
            api_key (str): Anthropic API key (defaults to environment variable)
            ocr_results_dir (str): Directory where OCR results are stored
        """
        self.batch_id = batch_id
        self.api_key = api_key if api_key else os.environ.get("ANTHROPIC_API_KEY")
        
        # Initialize the Claude client
        self.client = anthropic.Anthropic(api_key=self.api_key)
        
        # Set up output directory
        if ocr_results_dir:
            self.ocr_results_dir = ocr_results_dir
        else:
            # Try to locate the standard directory structure
            current_file = Path(__file__)
            project_root = current_file.parent.parent  # Go up one level
            self.ocr_results_dir = os.path.join(project_root, "data", "ocr_results")
    
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
            dict: Structured dictionary with question information
        """
        result = {}
        question_num = 1
        
        # Split the response by double newlines to get each question block
        blocks = response.strip().split('\n\n')
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) != 3:
                continue  # Skip invalid blocks
                
            question_data = {}
            for line in lines:
                if line.startswith("question_start:"):
                    question_data["question_start"] = line.replace("question_start:", "").strip()
                elif line.startswith("question_type:"):
                    question_data["question_type"] = line.replace("question_type:", "").strip()
                elif line.startswith("sub_questions_independent:"):
                    value = line.replace("sub_questions_independent:", "").strip()
                    if value.lower() == "true":
                        question_data["sub_questions_independent"] = True
                    elif value.lower() == "false":
                        question_data["sub_questions_independent"] = False
                    else:
                        question_data["sub_questions_independent"] = None
            
            # Only add if we have all three fields
            if len(question_data) == 3:
                result[str(question_num)] = question_data
                question_num += 1
            
        return result
    
    def _save_result(self, file_path, result):
        """
        Save the parsed result as a JSON file.
        
        Args:
            file_path (str): The original file path
            result (dict): The parsed result to save
            
        Returns:
            bool: Whether the save was successful
        """
        try:
            # Get the base name of the .mmd file (without extension)
            file_base_name = Path(file_path).stem
            
            # Create output file path in the same directory as the input
            output_dir = os.path.dirname(file_path)
            output_file = os.path.join(output_dir, f"{file_base_name}_post1.json")
            
            # Save the result as JSON
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2)
            
            print(f"Successfully saved result to {output_file}")
            return True
        except Exception as e:
            print(f"Error saving result for {file_path}: {str(e)}")
            return False
    
    async def retrieve_batch(self):
        """
        Retrieve and process the results from a completed batch.
        
        Returns:
            tuple: (success count, failure count)
        """
        success_count = 0
        failure_count = 0
        file_results = []
        
        try:
            # Check the batch status first
            batch_status = self.client.messages.batches.retrieve(self.batch_id)
            print(f"Batch {self.batch_id} status: {batch_status.processing_status}")
            print(f"Counts: {batch_status.request_counts}")
            
            if batch_status.processing_status != "ended":
                print(f"Batch processing has not ended yet. Current status: {batch_status.processing_status}")
                return 0, 0
            
            # Process the results
            print("Processing batch results...")
            
            # Create a directory to save raw results for debugging
            debug_dir = os.path.join(os.path.dirname(os.path.dirname(self.ocr_results_dir)), "debug_results")
            os.makedirs(debug_dir, exist_ok=True)
            
            # Stream the results from the batch
            for result in self.client.messages.batches.results(self.batch_id):
                custom_id = result.custom_id
                
                # Print result info for debugging
                print(f"\nResult for {custom_id}:")
                print(f"Result type: {result.result.type}")
                
                if result.result.type == "succeeded":
                    try:
                        # Extract text content from the message
                        message = result.result.message
                        
                        # Extract the text content
                        content_text = self._extract_text_from_content(message.content)
                        
                        # Parse the response
                        parsed_result = self._parse_claude_response(content_text)
                        
                        print(f"Parsed {len(parsed_result)} questions from result")
                        
                        # For demonstration purposes, print the first question
                        if parsed_result and "1" in parsed_result:
                            print(f"First question: {parsed_result['1']}")
                        
                        # Store the result for later processing
                        file_results.append({
                            "custom_id": custom_id,
                            "content_text": content_text,
                            "parsed_result": parsed_result
                        })
                        
                        success_count += 1
                    except Exception as e:
                        print(f"Error parsing result for {custom_id}: {str(e)}")
                        failure_count += 1
                else:
                    # Handle error cases
                    error_type = result.result.type
                    error_message = ""
                    if error_type == "errored" and hasattr(result.result, "error"):
                        error_message = result.result.error.message if hasattr(result.result.error, "message") else str(result.result.error)
                    
                    print(f"Failed to process {custom_id}: {error_type} - {error_message}")
                    failure_count += 1
            
            # Save raw debug output of just the text content and parsed results
            with open(os.path.join(debug_dir, f"batch_{self.batch_id}_content.txt"), 'w', encoding='utf-8') as f:
                for result in file_results:
                    f.write(f"=== {result['custom_id']} ===\n")
                    f.write(result['content_text'])
                    f.write("\n\n")
            
            # Now let's process and save each result
            print("\n\nNow we'll process and save each result.")
            print(f"We have {len(file_results)} successful results to save.")
            
            for i, result_data in enumerate(file_results):
                print(f"\nProcessing result {i+1}/{len(file_results)} (from {result_data['custom_id']}):")
                
                # Get file path from user
                file_path = input(f"Enter the file path for {result_data['custom_id']}: ").strip()
                
                if not file_path:
                    # Try to auto-detect
                    for root, _, files in os.walk(self.ocr_results_dir):
                        for file in files:
                            if file.endswith('.mmd'):
                                path = os.path.join(root, file)
                                print(f"Found .mmd file: {path}")
                                choice = input("Use this file? (y/n): ").strip().lower()
                                if choice == 'y':
                                    file_path = path
                                    break
                        if file_path:
                            break
                
                if not file_path:
                    print("No file path provided, skipping this result.")
                    continue
                
                # Save the result
                if self._save_result(file_path, result_data['parsed_result']):
                    print(f"Successfully saved result for {file_path}")
                else:
                    print(f"Failed to save result for {file_path}")
            
            return success_count, failure_count
        
        except Exception as e:
            print(f"Error retrieving batch results: {str(e)}")
            import traceback
            traceback.print_exc()
            return 0, 0


async def main():
    # Get batch ID from user
    batch_id = input("Enter the batch ID to retrieve: ").strip()
    
    if not batch_id:
        print("No batch ID provided, exiting.")
        return
    
    # Create the batch retriever
    retriever = BatchRetriever(batch_id)
    
    # Process the batch
    success, failed = await retriever.retrieve_batch()
    print(f"\nBatch retrieval completed: {success} successful results processed, {failed} failed")


if __name__ == "__main__":
    asyncio.run(main())