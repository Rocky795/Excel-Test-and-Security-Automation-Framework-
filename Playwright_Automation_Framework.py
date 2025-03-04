# File: parallel_runner.py
import concurrent.futures
import os
import time
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple

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

def execute_test_case(page, object_repo, test_case: Dict[str, Any], test_logger,timestamp=None) -> Dict[str, Any]:
    """Execute a single test case using an existing browser session"""
    test_id = test_case["test_id"]
    test_name = test_case["test_name"]
    
    # Log test case start
    test_logger.info(f"Starting execution of test case: [{test_id}] {test_name}")
    
    # Create context for variable storage
    context_vars = {}
    
    # Take screenshot before test
    screenshot_dir=f"test_results/test_results_{timestamp}"
    os.makedirs(screenshot_dir, exist_ok=True)
    screenshot_path = f"{screenshot_dir}/befor{test_id}_{int(time.time())}.png"
    page.screenshot(path=screenshot_path)
    test_logger.info(f"Initial screenshot saved: {screenshot_path}")
    
    # Track if test case passed
    test_passed = True
    failed_steps = []
    start_time = time.time()
    
    # Initialize page actions
    page_actions = PageActions(page, object_repo,test_logger)
    
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
            "screenshot_path":screenshot_path,
           
        }
    else:
        test_logger.error(f"Test case [{test_id}] {test_name} FAILED (Execution time: {execution_time:.2f}s)")
        result = {
            "test_id": test_id,
            "test_name": test_name,
            "status": "FAILED",
            "execution_time": execution_time,
            "failed_steps": failed_steps,
            "screenshot_path":screenshot_path,
        }    
    
    return result

def execute_excel_file(test_case_file: str,timestamp=None) -> List[Dict[str, Any]]:
    """Execute all test cases from a single Excel file in one thread"""
    excel_filename = os.path.basename(test_case_file)
    
    # Create a specific logger for this excel file
    file_logger = logging.getLogger(f"ExcelFile_{excel_filename}")
    log_file = f"logs/excel_{excel_filename}_{int(time.time())}.log"
    os.makedirs("logs", exist_ok=True)
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    file_logger.addHandler(file_handler)
    
    file_logger.info(f"Starting execution of all test cases from file: {excel_filename}")
    
    results = []
    
    try:
        # Load test cases from Excel
        excel_reader = ExcelReader(test_case_file)
        test_cases = excel_reader.read_test_cases()
        
        # Filter enabled test cases
        enabled_test_cases = [tc for tc in test_cases if tc.get("enabled", True)]
        if not enabled_test_cases:
            file_logger.warning(f"No enabled test cases found in {excel_filename}")
            return results
            
        file_logger.info(f"Loaded {len(enabled_test_cases)} enabled test cases from {excel_filename}")
        
        # Setup browser and login once for all test cases in this file
        playwright, browser, context, page = setup_browser()
        login_to_salesforce(page)
        
        # Initialize object repository once
        object_repo = ObjectRepository("./object_repository/salesforce_objects.json", file_logger)
        
        # Execute each test case in sequence using the same browser session
        for test_case in enabled_test_cases:
            try:
                test_id = test_case["test_id"]
                # Create a unique logger for this test case
                test_case_logger = logging.getLogger(f"ExcelFile_{excel_filename}.TestCase_{test_id}")
                test_case_logger.setLevel(logging.INFO)
                
                # Create a unique log file name for the test case
                test_log_file = os.path.join("logs", f"{excel_filename}_TestCase_{test_id}_{int(time.time())}.log")
                file_handler = logging.FileHandler(test_log_file)
                file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
                
                # Clear existing handlers to avoid duplicate logs
                if test_case_logger.hasHandlers():
                    test_case_logger.handlers.clear()
                test_case_logger.addHandler(file_handler)

                # Execute the test case using the test-case-specific logger
                result = execute_test_case(page, object_repo, test_case, test_case_logger,timestamp)
                result["file"] = excel_filename
                result["log_file"] = test_log_file
                results.append(result)
                
                file_logger.info(f"Completed test case: [{result['test_id']}] {result['test_name']} - {result['status']}")
                
                # Remove and close the test case handler to avoid interference with other test cases
                test_case_logger.removeHandler(file_handler)
                file_handler.close()

            except Exception as e:
                file_logger.exception(f"Exception executing test case [{test_case['test_id']}]: {str(e)}")
                results.append({
                    "test_id": test_case["test_id"],
                    "test_name": test_case["test_name"],
                    "status": "ERROR",
                    "error": str(e),
                    "file": excel_filename,
                    "log_file": test_log_file,
                    "screenshot": None
                })
        
    except Exception as e:
        file_logger.exception(f"Exception occurred while processing file {excel_filename}: {str(e)}")
        
    finally:
        # Cleanup resources
        try:
            context.close()
            browser.close()
            playwright.stop()
        except Exception as cleanup_error:
            file_logger.error(f"Error during cleanup: {str(cleanup_error)}")
    
    file_logger.info(f"Completed execution of all test cases from file: {excel_filename}")
    return results

def run_tests_in_parallel(max_workers: int = 8):
    """Run each Excel file in its own thread, with a maximum of specified workers"""
    # Get all test case files
    test_cases_dir = "./test_cases"
    if not os.path.exists(test_cases_dir):
        os.makedirs(test_cases_dir)
        logger.info(f"Created directory: {test_cases_dir}")
        return []
    
    test_case_files = [
        os.path.join(test_cases_dir, f) 
        for f in os.listdir(test_cases_dir) 
        if f.endswith(('.xlsx', '.xls'))
    ]
    
    if not test_case_files:
        logger.warning("No test case files found in ./test_cases directory")
        return []
    
    # Create results directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = f"test_results/test_results_{timestamp}"
    os.makedirs(results_dir, exist_ok=True)
    
    logger.info(f"Total Excel files to process: {len(test_case_files)}")
    
    # Execute Excel files in parallel
    all_results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all Excel files
        future_to_file = {
            executor.submit(execute_excel_file, file,timestamp): file 
            for file in test_case_files
        }
        
        # Process results as they complete
        for future in concurrent.futures.as_completed(future_to_file):
            file = future_to_file[future]
            file_name = os.path.basename(file)
            try:
                results = future.result()
                all_results.extend(results)
                
                # Calculate file-level statistics
                total_in_file = len(results)
                passed = sum(1 for r in results if r["status"] == "PASSED")
                failed = sum(1 for r in results if r["status"] == "FAILED")
                errors = sum(1 for r in results if r["status"] == "ERROR")
                
                logger.info(f"Completed Excel file: {file_name} - "
                           f"Total: {total_in_file}, Passed: {passed}, Failed: {failed}, Errors: {errors}")
                
            except Exception as e:
                logger.error(f"Exception processing Excel file {file_name}: {str(e)}")
    
    # Save overall results to file
    # results_file = os.path.join(results_dir, "results.json")
    # with open(results_file, 'w') as f:
    #     json.dump(all_results, f, indent=2)
    # logger.info(f"Test results saved to {results_file}")
    
    
    return all_results,results_dir,timestamp

if __name__ == "__main__":
    # Create directory structure
    for directory in ["logs", "screenshots", "videos", "test_cases", "test_results", "object_repository"]:
        os.makedirs(directory, exist_ok=True)
    
    # Run tests in parallel
    max_threads = int(os.getenv("MAX_THREADS", "8"))
    logger.info(f"Starting test execution with {max_threads} parallel threads (one thread per Excel file)")
    
    results,results_dir,timestamp = run_tests_in_parallel(max_workers=max_threads)
    
    
    report = GenerateReport(results, results_dir, timestamp)
    html_report, json_report = report.generate_report()

    print(f"HTML report generated at: {html_report}")
    print(f"JSON report generated at: {json_report}")
    
    

    # Print summary to console
    if results:
        total = len(results)
        passed = sum(1 for r in results if r["status"] == "PASSED")
        failed = sum(1 for r in results if r["status"] == "FAILED")
        errors = sum(1 for r in results if r["status"] == "ERROR")
        
        # Group results by file
        results_by_file = {}
        for r in results:
            file = r.get("file", "Unknown")
            if file not in results_by_file:
                results_by_file[file] = []
            results_by_file[file].append(r)
        
        logger.info("=" * 80)
        logger.info("TEST EXECUTION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total Excel files processed: {len(results_by_file)}")
        logger.info(f"Total test cases: {total}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Errors: {errors}")
        logger.info(f"Success rate: {(passed/total)*100:.2f}%" if total > 0 else "0%")
        
        # Print file-level statistics
        logger.info("-" * 80)
        logger.info("RESULTS BY FILE")
        logger.info("-" * 80)
        for file, file_results in results_by_file.items():
            file_total = len(file_results)
            file_passed = sum(1 for r in file_results if r["status"] == "PASSED")
            logger.info(f"{file}: {file_passed}/{file_total} passed ({(file_passed/file_total)*100:.2f}%)")