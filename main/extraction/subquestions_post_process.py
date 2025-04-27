import os
import json
import re
import asyncio
import time
from pathlib import Path
import anthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request
from tqdm import tqdm
import streamlit as st


class SubQuestionPostProcessor:
    def __init__(self, root_dir=None, api_key=None, batch_size=20, model="claude-3-7-sonnet-20250219"):
        """
        Initialize the sub-question post-processor for evaluating question independence.
        
        Args:
            root_dir (str): The root directory of the project
            api_key (str): API key for Anthropic
            batch_size (int): Maximum number of requests to process in a batch
            model (str): Claude model to use for processing
        """
        self.root_dir = root_dir if root_dir else self._get_project_root()
        self.api_key = st.secrets["ANTHROPIC_API_KEY"]
        self.batch_size = batch_size
        self.model = model
        
        # Initialize the Claude client
        self.client = anthropic.Anthropic(api_key=self.api_key)
        
        # Set up file paths
        self.question_bank_path = os.path.join(self.root_dir, "results_question_bank", "question_bank.json")
        self.prompt_path = os.path.join(self.root_dir, "prompts", "sub_ques_dependency.txt")
        
        # Load the prompt template
        self.prompt_template = self._load_prompt_template()
        
    def _get_project_root(self):
        """Determine the project root based on the current file location."""
        current_file = Path(__file__)
        return current_file.parent.parent.parent  # Go up two levels to reach project root
    
    def _load_prompt_template(self):
        """Load the prompt template from the specified file."""
        try:
            with open(self.prompt_path, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            print(f"Error: Prompt file not found at {self.prompt_path}")
            return None
        
    def _prepare_prompt(self, question_text):
        """Prepare the prompt by replacing the placeholder with the actual question text."""
        if not self.prompt_template:
            raise ValueError("Prompt template is not loaded")
        
        return self.prompt_template.replace("{{question_text}}", question_text)
    
    def _load_question_bank(self):
        """Load the question bank from the JSON file."""
        try:
            with open(self.question_bank_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Error: Question bank not found at {self.question_bank_path}")
            return []
        except json.JSONDecodeError:
            print(f"Error: Unable to parse question bank JSON")
            return []
    
    def _save_question_bank(self, question_bank):
        """Save the updated question bank to the JSON file."""
        try:
            with open(self.question_bank_path, 'w', encoding='utf-8') as file:
                json.dump(question_bank, file, indent=2)
            return True
        except Exception as e:
            print(f"Error saving question bank: {str(e)}")
            return False
    
    def _parse_claude_response(self, content_text):
        """
        Parse Claude's response to extract the JSON evaluation result.
        
        Args:
            content_text (str): The text response from Claude
            
        Returns:
            dict: Parsed JSON response with independence evaluation
        """
        try:
            # Find JSON in the response using regex to extract valid JSON objects
            json_pattern = r'(\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\})'
            json_matches = re.findall(json_pattern, content_text)
            
            if json_matches:
                # Try each match until we find a valid JSON that has our expected structure
                for json_str in json_matches:
                    try:
                        result = json.loads(json_str)
                        # Check if it has the expected keys
                        if "sub_questions_independent" in result:
                            return result
                    except json.JSONDecodeError:
                        continue
                
                # If we get here, none of the matches had our expected structure
                print(f"Found JSON objects but none had the expected 'sub_questions_independent' key")
                return None
            else:
                print(f"Error: No JSON objects found in response")
                print(f"Response preview: {content_text[:200]}...")
                return None
        except Exception as e:
            print(f"Error parsing Claude response: {str(e)}")
            return None
    
    def _extract_sub_questions(self, question_text, question_starts):
        """
        Extract complete sub-questions from the original question text.
        
        Args:
            question_text (str): The full text of the question
            question_starts (list): List of starting strings for each sub-question
            
        Returns:
            list: List of complete sub-question texts
        """
        sub_questions = []
        
        # Create a list of starting positions for each sub-question
        start_positions = []
        for start_str in question_starts:
            # Use a more precise method to find the exact position of each start string
            # This ensures we don't match partial strings (e.g., "1. " vs "11. ")
            escaped_start = re.escape(start_str)
            matches = list(re.finditer(f"(?<![0-9\\w]){escaped_start}", question_text))
            if matches:
                start_positions.append(matches[0].start())
        
        # Sort start positions in ascending order
        start_positions.sort()
        
        # Extract each sub-question based on start and end positions
        for i, start_pos in enumerate(start_positions):
            # Determine end position (either next sub-question or end of text)
            if i < len(start_positions) - 1:
                end_pos = start_positions[i+1]
            else:
                end_pos = len(question_text)
            
            # Extract the sub-question text
            sub_question = question_text[start_pos:end_pos].strip()
            sub_questions.append(sub_question)
        
        return sub_questions
    
    async def _evaluate_single_question(self, question):
        """
        Evaluate a single question for independence (non-batch method).
        
        Args:
            question (dict): The question dictionary
            
        Returns:
            tuple: (Question, evaluation result)
        """
        try:
            question_text = question.get("question_text", "")
            
            # Skip if no question text
            if not question_text:
                print(f"Warning: Question {question.get('question_number')} has no text. Skipping.")
                return question, None
            
            # Prepare the prompt
            prompt = self._prepare_prompt(question_text)
            
            # Send to Claude API with thinking enabled
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=1,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                thinking={
                    "type": "enabled",
                    "budget_tokens": 1024
                }
            )
            
            # Extract text content from the response
            if hasattr(message, 'content'):
                if isinstance(message.content, list):
                    # For content blocks, extract only text blocks
                    content_text = ""
                    for block in message.content:
                        if hasattr(block, 'type') and block.type == 'text' and hasattr(block, 'text'):
                            content_text += block.text
                        elif isinstance(block, dict) and block.get('type') == 'text':
                            content_text += block.get('text', '')
                else:
                    # For single content object
                    content_text = str(message.content)
            else:
                # Fallback to string representation
                content_text = str(message)
            
            # Parse the response to get the evaluation result
            result = self._parse_claude_response(content_text)
            
            return question, result
            
        except Exception as e:
            print(f"Error evaluating question {question.get('question_number')}: {str(e)}")
            return question, None
    
    async def _process_batch(self, questions_batch):
        """
        Process a batch of questions using Claude's batch API.
        
        Args:
            questions_batch (list): List of question dictionaries to process
            
        Returns:
            list: List of tuples with (question, result)
        """
        # Create question map using custom_id as key
        question_map = {}
        batch_requests = []
        
        # Prepare batch requests
        for idx, question in enumerate(questions_batch):
            try:
                # Create a unique custom_id for this question
                custom_id = f"question_{idx}"
                question_map[custom_id] = question
                
                # Get the question text
                question_text = question.get("question_text", "")
                
                # Skip if no question text
                if not question_text:
                    print(f"Warning: Question {question.get('question_number')} has no text. Skipping.")
                    continue
                
                # Prepare the prompt
                prompt = self._prepare_prompt(question_text)
                
                # Add to batch requests
                batch_requests.append(
                    Request(
                        custom_id=custom_id,
                        params=MessageCreateParamsNonStreaming(
                            model=self.model,
                            max_tokens=4096,
                            temperature=1,
                            messages=[
                                {
                                    "role": "user",
                                    "content": prompt
                                }
                            ],
                            thinking={
                                "type": "enabled",
                                "budget_tokens": 1024
                            }
                        )
                    )
                )
            except Exception as e:
                print(f"Error preparing batch request for question {question.get('question_number')}: {str(e)}")
        
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
                question = question_map.get(custom_id)
                
                if question is None:
                    print(f"Warning: Could not find question for custom_id {custom_id}")
                    continue
                
                if result.result.type == "succeeded":
                    try:
                        # Extract text content from the message
                        message = result.result.message
                        
                        # Extract content text based on the structure
                        content_text = ""
                        if hasattr(message, 'content'):
                            if isinstance(message.content, list):
                                for block in message.content:
                                    if hasattr(block, 'text'):
                                        content_text += block.text
                            else:
                                content_text = str(message.content)
                        
                        # Parse the response
                        evaluation_result = self._parse_claude_response(content_text)
                        results.append((question, evaluation_result))
                        
                        print(f"Successfully processed question {question.get('question_number')}")
                    except Exception as e:
                        print(f"Error parsing result for question {question.get('question_number')}: {str(e)}")
                        results.append((question, None))
                else:
                    # Handle error cases
                    error_type = result.result.type
                    error_message = ""
                    if error_type == "errored" and hasattr(result.result, "error"):
                        error_message = result.result.error.message if hasattr(result.result.error, "message") else str(result.result.error)
                    
                    print(f"Failed to process question {question.get('question_number')}: {error_type} - {error_message}")
                    results.append((question, None))
            
            return results
        except Exception as e:
            print(f"Error processing batch: {str(e)}")
            # Fall back to individual processing if batch fails
            print("Falling back to individual processing...")
            results = []
            for question in questions_batch:
                question_result = await self._evaluate_single_question(question)
                results.append(question_result)
            return results
    
    async def run_async(self):
        """
        Run the sub-question post-processing pipeline asynchronously with batch processing.
        
        Returns:
            tuple: (processed count, updated count, extracted count)
        """
        processed_count = 0
        updated_count = 0
        extracted_count = 0
        
        # Load the question bank
        question_bank = self._load_question_bank()
        if not question_bank:
            print("Question bank is empty or could not be loaded. Exiting.")
            return processed_count, updated_count, extracted_count
        
        # Identify questions to process (where sub_questions_independent is True)
        to_process = [q for q in question_bank if q.get("sub_questions_independent") is True]
        
        print(f"Found {len(to_process)} questions with sub_questions_independent=True")
        
        # Create a list to store questions to be deleted after processing
        to_delete = []
        # Create a list to store new sub-questions to be added
        new_questions = []
        
        # Process questions in batches
        for i in range(0, len(to_process), self.batch_size):
            batch = to_process[i:i + self.batch_size]
            print(f"\nProcessing batch {i//self.batch_size + 1} of {(len(to_process) + self.batch_size - 1)//self.batch_size} ({len(batch)} questions)")
            
            # Process the batch
            batch_results = await self._process_batch(batch)
            
            # Handle the results
            for question, result in batch_results:
                processed_count += 1
                
                if not result:
                    print(f"Warning: Failed to evaluate question {question.get('question_number')}. Skipping.")
                    continue
                
                # Handle the result
                independence = result.get("sub_questions_independent", False)
                
                if not independence:
                    # Update the original question
                    question["sub_questions_independent"] = False
                    updated_count += 1
                    print(f"Updated question {question.get('question_number')}: sub_questions_independent=False")
                else:
                    # Extract and create new sub-questions
                    question_starts = result.get("question_starts", [])
                    sub_questions = self._extract_sub_questions(question.get("question_text", ""), question_starts)
                    
                    if sub_questions:
                        # Mark original question for deletion
                        to_delete.append(question)
                        
                        # Create new entries for each sub-question
                        for i, sub_q_text in enumerate(sub_questions):
                            # Create a new question based on the original
                            new_question = {
                                "question_number": f"{question.get('question_number')}.{i+1}",
                                "question_text": sub_q_text,
                                "question_type": question.get("question_type"),
                                "sub_questions_independent": None,  # Set to null for sub-questions
                                "source_pdf": question.get("source_pdf"),
                                "source_file": question.get("source_file")
                            }
                            
                            new_questions.append(new_question)
                            extracted_count += 1
                        
                        print(f"Extracted {len(sub_questions)} sub-questions from question {question.get('question_number')}")
        
        # Remove questions marked for deletion
        for question in to_delete:
            if question in question_bank:
                question_bank.remove(question)
        
        # Add new sub-questions
        question_bank.extend(new_questions)
        
        # Save the updated question bank
        save_success = self._save_question_bank(question_bank)
        
        if save_success:
            print(f"Successfully updated question bank: {len(to_delete)} questions deleted, {len(new_questions)} sub-questions added")
        else:
            print("Failed to save updated question bank")
        
        return processed_count, updated_count, extracted_count
    
    def run(self):
        """
        Run the sub-question post-processing pipeline with batch processing.
        This is a synchronous wrapper around the async run_async method.
        
        Returns:
            tuple: (processed count, updated count, extracted count)
        """
        try:
            # Create and run an event loop to execute the async method
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # If there's no event loop in the current thread, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            # Run the async method in the event loop
            return loop.run_until_complete(self.run_async())
        finally:
            # Close the event loop if we created a new one
            if not loop.is_running():
                loop.close()


if __name__ == "__main__":
    # Run the processor directly if this script is executed
    processor = SubQuestionPostProcessor()
    processed, updated, extracted = processor.run()
    print(f"\nSub-question post-processing completed: {processed} questions processed")
    print(f"  - {updated} questions had independence flag updated")
    print(f"  - {extracted} sub-questions were extracted")