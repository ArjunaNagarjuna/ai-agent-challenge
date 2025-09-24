# AI Agent for Bank Statement Parsing

This project contains an AI agent (`agent.py`) that automatically writes, tests, and debugs a Python parser for bank statement PDFs. The agent uses the Groq API to generate code and operates in a self-correcting loop to achieve its goal.

The final, human-corrected parser for the ICICI bank statement is located at `custom_parsers/icici_parser.py`, and it is verified by the test script `test_parser.py`.

## 🤖 Agent Architecture

The agent operates in a simple "generate-test-correct" loop:

1.  **Plan & Generate**: The agent is given a detailed prompt with context (PDF text sample, target CSV schema, and specific parsing rules) and asked to write a Python parser file.
2.  **Execute & Test**: The generated Python file is saved and executed in a secure subprocess. Its output DataFrame is compared against the ground-truth `result.csv`.
3.  **Observe & Self-Correct**: If the test fails, the error message is captured and fed back into the prompt. The agent is then asked to fix its previous mistake. This loop runs for a predefined number of attempts.

## 🚀 How to Run

Follow these 5 steps to run the final, working test.



1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd ai-agent-challenge
    ```

    

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up your API key:**
    Create a `.env` file in the root directory and add your Groq API key:
    ```
    GROQ_API_KEY="your-groq-api-key"
    ```

5.  **Run the verification test:**
    To confirm that the final, human-corrected parser works perfectly, run the dedicated test script:
    ```bash
    pytest
    ```
    You should see a "1 passed" message, confirming the parser is correct.

## 🛠️ Development Journey

This project was built through a step-by-step debugging process that solved numerous real-world coding challenges.


* **Step 1: Initial Setup**: The project structure was created, dependencies were installed, and the initial `agent.py` script was written.
  

* **Step 2: Solving API Errors**: The agent initially failed to connect to the Groq API. We fixed this by identifying and updating the correct LLM model name after several "decommissioned" or "not found" errors.

  
* **Step 3: Debugging the Agent's Test Harness**: Once connected, the agent's internal testing logic had bugs. We fixed these by printing hidden error messages, correcting `NameError` and `SyntaxError` issues, and improving the AI's response cleaning logic.


* **Step 4: Iterative Prompt Engineering**: The agent consistently failed to generate a correct parser. We improved the prompt by adding more specific rules, "few-shot" examples, and a crucial rule describing the exact text pattern of a transaction line.


* **Step 5: Manual Intervention and Final Validation**: When the agent still struggled, the final solution involved:
    * Writing a robust, human-coded parser in `custom_parsers/icici_parser.py`.
    * Creating a dedicated test file, `test_parser.py`, to directly validate the parser.
    * Fixing a `FileNotFoundError` by using absolute paths in the test script.
    * Running `pytest` to confirm the solution works, resulting in a "1 passed" success message.
