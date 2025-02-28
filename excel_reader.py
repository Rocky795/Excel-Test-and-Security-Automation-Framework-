# File: excel_reader.py
import pandas as pd
import openpyxl
import re
import os
from typing import List, Dict, Any


class ExcelReader:
    def __init__(self, file_path: str):
        """Initialize the Excel reader with file path"""
        self.file_path = file_path
        self._validate_file()

    def _validate_file(self):
        """Validate that the Excel file exists and has the right format"""
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Test case file not found: {self.file_path}")

        # Check file extension
        if not self.file_path.endswith(('.xlsx', '.xls')):
            raise ValueError(f"File must be an Excel file (.xlsx or .xls): {self.file_path}")

    def read_test_cases(self) -> List[Dict[str, Any]]:
        """Read all test cases from Excel file"""
        try:
            # Load the workbook and first sheet
            df = pd.read_excel(self.file_path)

            # Verify required columns exist
            required_columns = ['Test ID', 'Test Name', 'Description']
            for column in required_columns:
                if column not in df.columns:
                    raise ValueError(f"Required column '{column}' not found in Excel file")

            # Get step columns (any column that starts with 'Step')
            step_columns = [col for col in df.columns if col.startswith('Step')]
            if not step_columns:
                raise ValueError("No step columns found in Excel file. Column names should start with 'Step'")

            # Process all test cases
            test_cases = []
            for idx, row in df.iterrows():
                test_case = {
                    "test_id": str(row.get("Test ID", "")),
                    "test_name": str(row.get("Test Name", "")),
                    "description": str(row.get("Description", "")),
                    "enabled": bool(row.get("Enabled", True)),  # Default to enabled if column doesn't exist
                    "steps": []
                }

                # Process steps
                for step_col in step_columns:
                    if pd.notna(row.get(step_col)) and str(row.get(step_col)).strip():
                        test_case["steps"].append(str(row.get(step_col)).strip())

                # Only include test case if it has at least one step
                if test_case["steps"]:
                    test_cases.append(test_case)

            print(f"Successfully loaded {len(test_cases)} test cases from {self.file_path}")
            return test_cases

        except Exception as e:
            print(f"Error reading Excel file: {e}")
            raise

