import anthropic

client = anthropic.Anthropic(
    # defaults to os.environ.get("ANTHROPIC_API_KEY")
    api_key="my_api_key",
)

# Replace placeholders like {{text_extract}} with real values,
# because the SDK does not support variables.
message = client.messages.create(
    model="claude-3-5-haiku-20241022",
    max_tokens=8192,
    temperature=1,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "[INST]\n<<SYS>>\nYou are an exam question locator, classifier, and sub-question assessor.\nTask  \n• Scan the document in <UserInput> and identify every main question.  \n  ‣ A main question is a line that starts with an integer plus a period, e.g., 1. 2..  \n• For each main question:\n  1. question_start – copy exactly the first 20 visible characters of the question line including its numbering, point value, punctuation, and spacing. If the line has fewer than 20 characters after the number, copy the entire line.\n  2. question_type – pick one label from this fixed list (case-sensitive):  \n     • True/False – asks for a true-or-false judgment.  \n     • Short Answer – expects a brief phrase or ≤ 2-sentence answer.  \n     • Theory – conceptual explanation without detailed computation.  \n     • Numerical – requires calculation and a numeric result.  \n     • Proof – demands a formal derivation or proof.  \n     • Comparison – explicitly asks to compare or contrast items.\n  3. sub_questions_independent – decide whether the lettered sub-parts (a), (b), … are independent tasks (can be solved separately without sharing intermediate results).  \n     • Output true  if every sub-question is independent of the others.  \n     • Output false if any sub-question depends on answers or work from another.  \n     • Output None if the main question has no sub-questions.\nRules  \n• Preserve original capitalization, spaces, math notation, etc., in the 20-character snippet.  \n• Produce no commentary.\n<</SYS>>\n<UserInput>\n{{text_extract}}\n</UserInput>\nOutput Instructions:\n1. For each main question output three lines in this exact order:  \n   question_start: <snippet>  \n   question_type: <type>  \n   sub_questions_independent: <true|false|None>  \n2. Insert one blank line between blocks for successive questions.  \n3. Do not output anything else—no extra headers, numbering, or explanations.\nOutput Example:\nquestion_start: 1. (13 points) Ass  \nquestion_type: Numerical  \nsub_questions_independent: true\nquestion_start: 2. (14 points) Ass  \nquestion_type: Numerical  \nsub_questions_independent: false\n[/INST]"
                }
            ]
        }
    ]
)
print(message.content)