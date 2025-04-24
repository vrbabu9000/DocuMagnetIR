import os
import json
import glob
from pathlib import Path


class QuestionBankGenerator:
    def __init__(self, root_dir=None):
        """
        Initialize the QuestionBankGenerator for creating a question bank from .mmd files.
        
        Args:
            root_dir (str): The root directory of the project
        """
        self.root_dir = root_dir if root_dir else self._get_project_root()
        
        # Set up directories
        self.ocr_results_dir = os.path.join(self.root_dir, "data", "ocr_results")
        self.output_dir = os.path.join(self.root_dir, "results_question_bank")
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize the question bank
        self.question_bank = []
        
    def _get_project_root(self):
        """Determine the project root based on the current file location."""
        current_file = Path(__file__)
        return current_file.parent  # Assuming this file is in the project root
    
    def _extract_questions_from_mmd(self, mmd_path, config_json, pdf_name):
        """
        Extract questions from an .mmd file using the configuration in _post1.json.
        
        Args:
            mmd_path (str): Path to the .mmd file
            config_json (dict): Configuration from _post1.json
            pdf_name (str): Name of the PDF folder
            
        Returns:
            list: List of extracted questions with metadata
        """
        # Read the content of the .mmd file
        with open(mmd_path, 'r', encoding='utf-8') as file:
            mmd_content = file.read()
        
        # Split the content by lines for processing
        lines = mmd_content.split('\n')
        
        # Sort question numbers to ensure we process in order
        question_numbers = sorted([int(qnum) for qnum in config_json.keys()])
        
        extracted_questions = []
        
        # Process each question
        for i, qnum in enumerate(question_numbers):
            qnum_str = str(qnum)
            
            # Get question configuration
            question_config = config_json[qnum_str]
            question_start_text = question_config["question_start"]
            question_type = question_config["question_type"]
            sub_questions_independent = question_config.get("sub_questions_independent", True)
            
            # Find the line where this question starts
            start_idx = None
            for j, line in enumerate(lines):
                if question_start_text in line:
                    start_idx = j
                    break
            
            if start_idx is None:
                print(f"Warning: Could not find start of question {qnum} in {mmd_path}")
                continue
            
            # Determine where this question ends
            end_idx = len(lines)
            if i < len(question_numbers) - 1:
                next_qnum = str(question_numbers[i + 1])
                next_question_start = config_json[next_qnum]["question_start"]
                
                # Find the line where the next question starts
                for j, line in enumerate(lines[start_idx+1:], start=start_idx+1):
                    if next_question_start in line:
                        end_idx = j
                        break
            
            # Extract the question text
            question_text = '\n'.join(lines[start_idx:end_idx])
            
            # Add to our extracted questions
            extracted_questions.append({
                "question_number": qnum,
                "question_text": question_text,
                "question_type": question_type,
                "sub_questions_independent": sub_questions_independent,
                "source_pdf": pdf_name,
                "source_file": os.path.basename(mmd_path)
            })
        
        return extracted_questions
    
    def process_ocr_results(self):
        """
        Process all OCR result folders and extract questions from .mmd files.
        
        Returns:
            int: Number of questions extracted
        """
        # Get all PDF folders in the OCR results directory
        pdf_folders = [f for f in os.listdir(self.ocr_results_dir) 
                      if os.path.isdir(os.path.join(self.ocr_results_dir, f))]
        
        total_questions = 0
        
        for pdf_folder in pdf_folders:
            folder_path = os.path.join(self.ocr_results_dir, pdf_folder)
            
            # Find pairs of .mmd and corresponding _post1.json files
            mmd_files = glob.glob(os.path.join(folder_path, "*.mmd"))
            
            for mmd_path in mmd_files:
                # Check if there's a corresponding _post1.json file
                file_base_name = os.path.basename(mmd_path).replace('.mmd', '')
                post1_path = os.path.join(folder_path, f"{file_base_name}_post1.json")
                
                if not os.path.exists(post1_path):
                    print(f"Skipping {mmd_path} - no corresponding _post1.json file found")
                    continue
                
                # Load the configuration
                with open(post1_path, 'r', encoding='utf-8') as f:
                    config_json = json.load(f)
                
                # Extract questions
                questions = self._extract_questions_from_mmd(mmd_path, config_json, pdf_folder)
                
                # Add to the question bank
                self.question_bank.extend(questions)
                total_questions += len(questions)
                
                print(f"Processed {mmd_path}: extracted {len(questions)} questions")
        
        return total_questions
    
    def save_question_bank(self, output_filename="question_bank.json"):
        """
        Save the question bank to a JSON file.
        
        Args:
            output_filename (str): Name of the output file
            
        Returns:
            str: Path to the saved file
        """
        output_path = os.path.join(self.output_dir, output_filename)
        
        # Save the question bank as JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.question_bank, f, indent=2)
        
        return output_path
    
    def run(self):
        """
        Run the question bank generation process.
        
        Returns:
            tuple: (output file path, number of questions)
        """
        print("Starting question bank generation...")
        
        # Process all .mmd files and extract questions
        num_questions = self.process_ocr_results()
        
        # Save the question bank
        output_path = self.save_question_bank()
        
        print(f"Question bank generation completed: {num_questions} questions extracted")
        print(f"Question bank saved to: {output_path}")
        
        return output_path, num_questions