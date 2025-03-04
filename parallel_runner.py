# File: parallel_runner.py
import concurrent.futures
import os
import time
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from excel_reader import ExcelReader
from object_repository import ObjectRepository
from enhanced_page_actions import PageActions
from playwright.sync_api import sync_playwright
from generate_report import GenerateReport

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_execution.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("SalesforceAutomation")

def setup_browser():
    """Setup a new browser instance and context"""
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=False, slow_mo=100)
    context = browser.new_context(
        record_video_dir="videos/",
        ignore_https_errors=True
    )
    page = context.new_page()
    page.on("console", lambda msg: logger.debug(f"Browser console: {msg.text}"))
    
    return playwright, browser, context, page

def login_to_salesforce(page):
    """Login to Salesforce"""
    from dotenv import load_dotenv
    load_dotenv()  # Load environment variables from .env file
    
    page.goto(os.getenv("SALESFORCE_URL", "https://login.salesforce.com/"))
    page.fill("#username", os.getenv("SALESFORCE_USERNAME", ""))
    page.fill("#password", os.getenv("SALESFORCE_PASSWORD", ""))
    page.click("#Login")
    
    # Wait for Salesforce to load
    page.wait_for_selector("xpath=//button[@title='App Launcher']", state="visible", timeout=60000)
    
    return page

def execute_test_case(test_case_file: str, test_case: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a single test case in its own thread"""
    test_id = test_case["test_id"]
    test_name = test_case["test_name"]
    
    # Create a specific logger for this test case
    test_logger = logging.getLogger(f"TestCase_{test_id}")
    log_file = f"logs/test_{test_id}_{int(time.time())}.log"
    os.makedirs("logs", exist_ok=True)
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    test_logger.addHandler(file_handler)
    
    # Log test case start
    test_logger.info(f"Starting execution of test case: [{test_id}] {test_name}")
    
    # Setup browser and login
    try:
        playwright, browser, context, page = setup_browser()
        login_to_salesforce(page)
        
        # Initialize components
        object_repo = ObjectRepository("./object_repository/salesforce_objects.json",test_logger)
        page_actions = PageActions(page, object_repo)
        
        
        # Create context for variable storage
        context_vars = {}
        
        # Take screenshot before test
        os.makedirs("screenshots", exist_ok=True)
        screenshot_path = f"screenshots/before_{test_id}_{int(time.time())}.png"
        page.screenshot(path=screenshot_path)
        test_logger.info(f"Initial screenshot saved: {screenshot_path}")
        
        # Track if test case passed
        test_passed = True
        failed_steps = []
        start_time = time.time()
        
        # Execute each step in the test case
        for i, step in enumerate(test_case["steps"]):
            step_num = i + 1
            test_logger.info(f"Executing Step {step_num}: {step}")
            
            # Execute the step
            step_start_time = time.time()
            result = page_actions.execute_action(step, context_vars)
            step_execution_time = time.time() - step_start_time
            
            # Log the result
            if result:
                test_logger.info(f"Step {step_num} passed ({step_execution_time:.2f}s)")
            else:
                test_logger.error(f"Step {step_num} failed ({step_execution_time:.2f}s)")
                test_passed = False
                failed_steps.append(f"Step {step_num}: {step}")
                
                # Take screenshot of failure
                failure_screenshot = f"screenshots/failure_{test_id}_step{step_num}_{int(time.time())}.png"
                page.screenshot(path=failure_screenshot)
                test_logger.error(f"Failure screenshot saved: {failure_screenshot}")
                
                # Stop test case execution if a step fails
                break
        
        # Take screenshot after test
        screenshot_path = f"screenshots/after_{test_id}_{int(time.time())}.png"
        page.screenshot(path=screenshot_path)
        test_logger.info(f"Final screenshot saved: {screenshot_path}")
        
        execution_time = time.time() - start_time
        
        # Record test case result
        if test_passed:
            test_logger.info(f"Test case [{test_id}] {test_name} PASSED (Execution time: {execution_time:.2f}s)")
            result = {
                "test_id": test_id,
                "test_name": test_name,
                "status": "PASSED",
                "execution_time": execution_time,
                "log_file": log_file
            }
        else:
            test_logger.error(f"Test case [{test_id}] {test_name} FAILED (Execution time: {execution_time:.2f}s)")
            result = {
                "test_id": test_id,
                "test_name": test_name,
                "status": "FAILED",
                "execution_time": execution_time,
                "failed_steps": failed_steps,
                "log_file": log_file
            }
        
    except Exception as e:
        test_logger.exception(f"Exception occurred while executing test case: {str(e)}")
        result = {
            "test_id": test_id,
            "test_name": test_name,
            "status": "ERROR",
            "error": str(e),
            "log_file": log_file
        }
    
    finally:
        # Cleanup resources
        try:
            context.close()
            browser.close()
            playwright.stop()
        except Exception as cleanup_error:
            test_logger.error(f"Error during cleanup: {str(cleanup_error)}")
    
    test_logger.info(f"Log file saved in {log_file}")
    
    return result

def run_tests_in_parallel(max_workers: int = 8):
    """Run test cases in parallel with the specified number of workers"""
    # Get all test case files
    test_cases_dir = "./test_cases"
    if not os.path.exists(test_cases_dir):
        os.makedirs(test_cases_dir)
        logger.info(f"Created directory: {test_cases_dir}")
        return
    
    test_case_files = [
        os.path.join(test_cases_dir, f) 
        for f in os.listdir(test_cases_dir) 
        if f.endswith(('.xlsx', '.xls'))
    ]
    
    if not test_case_files:
        logger.warning("No test case files found in ./test_cases directory")
        return
    
    # Create results directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = f"test_results/test_results_{timestamp}"
    os.makedirs(results_dir, exist_ok=True)
    
    # Collect all test cases
    all_test_cases = []
    for test_case_file in test_case_files:
        try:
            excel_reader = ExcelReader(test_case_file)
            test_cases = excel_reader.read_test_cases()
            
            # Add file information to each test case
            for test_case in test_cases:
                test_case["file"] = test_case_file
                
            # Add enabled test cases to the list
            enabled_test_cases = [tc for tc in test_cases if tc.get("enabled", True)]
            all_test_cases.extend(enabled_test_cases)
            
            logger.info(f"Loaded {len(enabled_test_cases)} enabled test cases from {test_case_file}")
            
        except Exception as e:
            logger.error(f"Error loading test cases from {test_case_file}: {str(e)}")
    
    logger.info(f"Total test cases to execute: {len(all_test_cases)}")
    
    # Execute test cases in parallel
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all test cases
        future_to_test_case = {
            executor.submit(execute_test_case, tc["file"], tc): tc 
            for tc in all_test_cases
        }
        
        # Process results as they complete
        for future in concurrent.futures.as_completed(future_to_test_case):
            test_case = future_to_test_case[future]
            try:
                result = future.result()
                results.append(result)
                logger.info(f"Completed test case: [{result['test_id']}] {result['test_name']} - {result['status']}")
            except Exception as e:
                logger.error(f"Exception executing test case [{test_case['test_id']}]: {str(e)}")
                results.append({
                    "test_id": test_case["test_id"],
                    "test_name": test_case["test_name"],
                    "status": "ERROR",
                    "error": str(e)
                })
    
    # Generate summary report
    GenerateReport.generate_report(results, results_dir, timestamp)
    
    return results

if __name__ == "__main__":
    # Create directory structure
    for directory in ["logs", "screenshots", "videos", "test_cases", "object_repository","test_results"]:
        os.makedirs(directory, exist_ok=True)
    
    # Run tests in parallel
    max_threads = int(os.getenv("MAX_THREADS", "8"))
    logger.info(f"Starting test execution with {max_threads} parallel threads")
    
    results = run_tests_in_parallel(max_workers=max_threads)
    
    # Print summary to console
    if results:
        total = len(results)
        passed = sum(1 for r in results if r["status"] == "PASSED")
        failed = sum(1 for r in results if r["status"] == "FAILED")
        errors = sum(1 for r in results if r["status"] == "ERROR")
        
        logger.info("=" * 80)
        logger.info("TEST EXECUTION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total test cases: {total}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Errors: {errors}")
        logger.info(f"Success rate: {(passed/total)*100:.2f}%" if total > 0 else "0%")