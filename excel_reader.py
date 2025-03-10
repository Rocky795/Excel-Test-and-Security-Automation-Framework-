# File: excel_reader.py
import pandas as pd
import openpyxl
import logging
import re
import os
from typing import List, Dict, Any


class ExcelReader:
    def __init__(self, file_path: str,logger:None):
        """Initialize the Excel reader with file path"""
        self.file_path = file_path
        self.logger = logger or logging.getLogger("SalesforceAutomation")  # Use provided logger or create a new one
        self._validate_file()

    def _validate_file(self):
        """Validate that the Excel file exists and has the right format"""
        if not os.path.exists(self.file_path):
            self.logger.error(f"Test case file not found: {self.file_path}")
            raise FileNotFoundError(f"Test case file not found: {self.file_path}")

        # Check file extension
        if not self.file_path.endswith(('.xlsx', '.xls')):
            self.logger.error(f"File must be an Excel file (.xlsx or .xls): {self.file_path}")
            raise ValueError(f"File must be an Excel file (.xlsx or .xls): {self.file_path}")
        
        self.logger.info(f"File validation passed for {self.file_path}")

    def read_test_cases(self) -> List[Dict[str, Any]]:
        """Read all test cases from Excel file"""
        try:
            # Load the workbook and first sheet
            self.logger.info(f"Loading Excel file: {self.file_path}")
            df = pd.read_excel(self.file_path)

            # Verify required columns exist
            required_columns = ['Test ID', 'Test Name', 'Description']
            for column in required_columns:
                if column not in df.columns:
                    self.logger.error(f"Required column '{column}' not found in Excel file")
                    raise ValueError(f"Required column '{column}' not found in Excel file")
            
            self.logger.info("Excel file loaded successfully")

            # Get step columns (any column that starts with 'Step')
            step_columns = [col for col in df.columns if col.startswith('Step')]
            if not step_columns:
                self.logger.error("No step columns found in Excel file. Column names should start with 'Step'")
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

            self.logger.info(f"Successfully loaded {len(test_cases)} test cases from {self.file_path}")
            return test_cases

        except Exception as e:
            self.logger.error(f"Error reading Excel file: {e}")
            raise

