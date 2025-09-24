import os
import subprocess
import pandas as pd
import argparse
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
import pdfplumber

# --- Configuration & Setup ---
MAX_ATTEMPTS = 3
TARGET_PARSER_PATH = "custom_parsers/icici_parser.py"
TARGET_CSV_PATH = "data/icici/result.csv"
TARGET_PDF_PATH = "data/icici/icici_sample.pdf"

def setup_environment():
    """Loads environment variables for the API key."""
    load_dotenv()
    if not os.getenv("GROQ_API_KEY"):
        raise ValueError("GROQ_API_KEY not found in .env file")

def get_llm():
    """Initializes and returns the Groq LLM client."""
    return ChatGroq(model_name="Llama-3.1-8B-Instant", temperature=0)

def get_pdf_text_sample(pdf_path):
    """Extracts text from the first page of the PDF to give the LLM context."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            first_page = pdf.pages[0]
            return first_page.extract_text()
    except Exception as e:
        print(f"Could not read PDF for context: {e}")
        return "Could not extract text."

# --- Agent Core Logic ---

def create_prompt_template():
    """Creates the prompt template for the LLM to generate the parser."""
    return ChatPromptTemplate.from_messages([
        ("system", 
         """You are a Python code generation engine. Your ONLY output should be raw Python code. Do not add any explanations, comments, or text that is not valid Python.

         Your task is to write a Python file containing one function: `parse(pdf_path: str) -> pd.DataFrame`.

         **CRITICAL RULES:**
         1.  Your output MUST be ONLY Python code. Nothing else.
         2.  Do not include markdown fences like ```python or ```.
         3.  Do not include any English explanations.
         4.  Use `pdfplumber` to read the PDF text line by line. Do not use table extraction tools.
         5.  The PDF has transaction data that begins after a header row.
         6.  A transaction line can be identified by its structure: the first word is a date, the last is a balance, and the second to last is an amount. Everything between the date and the amount is the description.
         7.  The final DataFrame must have these exact columns: ['Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance'].
         8.  Convert amount columns to float and fill missing values with 0.0.
         """),
        ("human", 
         """
         Here is the context for the task:

         **Target DataFrame Schema (from the ground truth CSV):**
         {schema}

         **Text Sample from the first page of the PDF:**
         ```
         {pdf_sample}
         ```

         **Example of expected output for a few rows:**
         A single transaction from the PDF might look like this when processed into a data row:
         - Date: '03-08-2024'
         - Description: 'IMPS UPI Payment Amazon'
         - Debit Amt: 3886.08
         - Credit Amt: 0.0
         - Balance: 4631.11

         Another example:
         - Date: '18-08-2024'
         - Description: 'Interest Credit Saving Account'
         - Debit Amt: 596.72
         - Credit Amt: 0.0
         - Balance: 11524.79
         
         Notice that for a debit transaction, the 'Credit Amt' can be 0, and vice-versa. The column names must be exactly 'Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance'.

         {error_feedback}

         Now, please generate the complete Python code for the `{parser_path}` file.
         """),
    ])

def generate_parser_code(llm, prompt, schema, pdf_sample, error_feedback=""):
    """Invokes the LLM to generate the parser code."""
    chain = prompt | llm
    response = chain.invoke({
        "parser_path": TARGET_PARSER_PATH,
        "schema": schema,
        "pdf_sample": pdf_sample,
        "error_feedback": error_feedback
    })
    
    # More robustly clean the response to ensure it's just code
    code = response.content.strip()
    
    # Remove markdown code fences and the word 'python'
    if code.startswith("```python"):
        code = code[9:]
    elif code.startswith("```"):
        code = code[3:]
        
    if code.endswith("```"):
        code = code[:-3]
        
    return code.strip()

def save_code_to_file(code):
    """Saves the generated code to the specified parser file."""
    # Remove all triple backticks from code
    code = code.replace("```", "")
    os.makedirs(os.path.dirname(TARGET_PARSER_PATH), exist_ok=True)
    with open(TARGET_PARSER_PATH, "w") as f:
        f.write(code)
    print(f"✅ Agent has written the parser to {TARGET_PARSER_PATH}")


def test_generated_parser():
    """
    Tests the generated parser by running it and comparing its output DataFrame
    with the ground truth CSV. Returns (is_correct, error_message).
    """
    try:
        # Use subprocess to run the parser in an isolated environment
        # This is safer and catches a wider range of errors
        script_to_run = f"""
import pandas as pd
import traceback  # <-- This was the missing line
from custom_parsers.icici_parser import parse

try:
    # Attempt to parse the PDF and load the expected CSV
    generated_df = parse('{TARGET_PDF_PATH}')
    expected_df = pd.read_csv('{TARGET_CSV_PATH}')
    
    # Compare the generated DataFrame with the expected one
    pd.testing.assert_frame_equal(generated_df.astype(str), expected_df.astype(str))
    
    # If the comparison passes, print SUCCESS
    print("SUCCESS")

except Exception as e:
    # If any error occurs during parsing or comparison, print the full traceback
    print(f"Execution Error:\\n{{traceback.format_exc()}}")
"""
        result = subprocess.run(['python', '-c', script_to_run], capture_output=True, text=True, timeout=30)
        
        if "SUCCESS" in result.stdout:
            return True, ""
        else:
            error = result.stderr if result.stderr else result.stdout
            return False, f"Testing failed. Error:\n{error}"

    except Exception as e:
        return False, f"An unexpected error occurred during testing: {e}"
# --- Main Execution ---

def main(target):
    print(f"🚀 Starting agent to build parser for: {target}")
    
    setup_environment()
    llm = get_llm()
    prompt = create_prompt_template()

    # Provide context to the LLM
    expected_df = pd.read_csv(TARGET_CSV_PATH)
    schema_info = str(expected_df.head().to_markdown())
    pdf_sample = get_pdf_text_sample(TARGET_PDF_PATH)
    
    error_feedback = ""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"\n--- 💡 Attempt {attempt}/{MAX_ATTEMPTS} ---")
        
        # 1. PLAN & GENERATE CODE
        print("🧠 Agent is thinking and generating code...")
        generated_code = generate_parser_code(llm, prompt, schema_info, pdf_sample, error_feedback)
        
        # 2. WRITE CODE TO FILE
        save_code_to_file(generated_code)
        
        # 3. TEST THE CODE
        print("🔬 Agent is testing the generated parser...")
        is_correct, error_message = test_generated_parser()
        
        # 4. OBSERVE & REFINE
        if is_correct:
            print("\n🎉 Success! The generated parser passed the tests.")
            print(f"You can now inspect the final parser at `{TARGET_PARSER_PATH}`.")
            break
        else:
            print(f"❌ Test failed. Agent will attempt to self-correct.")
            # Add these lines to see the error
            print("\n--- Error Details ---")
            print(error_message)
            print("---------------------\n")
            
            error_feedback = f"The previous attempt failed. Here is the error message:\n{error_message}\nPlease analyze the error and provide a corrected version of the code."
            if attempt == MAX_ATTEMPTS:
                print("\n😞 Agent failed to generate a correct parser after all attempts.")
            
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Agent to generate PDF parsers.")
    parser.add_argument("--target", type=str, required=True, help="The name of the bank to target (e.g., 'icici').")
    args = parser.parse_args()
    
    main(args.target)