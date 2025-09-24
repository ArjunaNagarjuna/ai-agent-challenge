# In arjuna/test_parser.py

import pandas as pd
import pytest
import os
# This line imports the 'parse' function from your other file
from custom_parsers.icici_parser import parse 

# Get the absolute path to the directory where this test file is located
current_dir = os.path.dirname(os.path.abspath(__file__))

def test_parser():
    """
    This function tests the icici_parser.
    """
    # Create absolute paths to the files
    pdf_path = os.path.join(current_dir, "data", "icici", "icici_sample.pdf")
    csv_path = os.path.join(current_dir, "data", "icici", "result.csv")

    # 1. Load the expected result from the CSV
    expected_df = pd.read_csv(csv_path)

    # 2. Run your parser to get the actual result
    actual_df = parse(pdf_path)

    # 3. Compare the two DataFrames
    pd.testing.assert_frame_equal(
        actual_df.astype(str), 
        expected_df.astype(str)
    )