# File: test_salesforce.py
import pytest
import os
import time
from excel_reader import ExcelReader
from object_repository import ObjectRepository
from page_actions import PageActions


def get_test_case_files():
    """Get all Excel test case files in the test_cases directory"""
    test_cases_dir = "./test_cases"
    if not os.path.exists(test_cases_dir):
        os.makedirs(test_cases_dir)
        print(f"Created directory: {test_cases_dir}")
        return []

    files = [
        os.path.join(test_cases_dir, f)
        for f in os.listdir(test_cases_dir)
        if f.endswith(('.xlsx', '.xls'))
    ]
    return files


@pytest.mark.parametrize("test_case_file", get_test_case_files())
def test_salesforce_from_excel(salesforce_login, test_case_file):
    """Test Salesforce functionality based on Excel test cases"""
    page = salesforce_login

    # Initialize components
    excel_reader = ExcelReader(test_case_file)
    object_repo = ObjectRepository("./object_repository/salesforce_objects.json")
    page_actions = PageActions(page, object_repo)

    # Read test cases
    test_cases = excel_reader.read_test_cases()

    # Track test results
    results = {
        "total": len(test_cases),
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "failures": []
    }

    # Execute each test case
    for test_case in test_cases:
        test_id = test_case["test_id"]
        test_name = test_case["test_name"]

        if not test_case.get("enabled", True):
            print(f"Skipping disabled test: [{test_id}] {test_name}")
            results["skipped"] += 1
            continue

        print(f"\n{'=' * 80}\nExecuting test case: [{test_id}] {test_name}\n{'=' * 80}")

        # Create context for variable storage
        context = {}

        # Take screenshot before test
        screenshot_path = f"screenshots/before_{test_id}_{int(time.time())}.png"
        os.makedirs("screenshots", exist_ok=True)
        page.screenshot(path=screenshot_path)

        # Track if test case passed
        test_passed = True
        failed_steps = []

        # Execute each step in the test case
        for i, step in enumerate(test_case["steps"]):
            step_num = i + 1
            print(f"\nStep {step_num}: {step}")

            # Execute the step
            start_time = time.time()
            result = page_actions.execute_action(step, context)
            execution_time = time.time() - start_time

            # Log the result
            if result:
                print(f"✓ Step {step_num} passed ({execution_time:.2f}s)")
            else:
                print(f"✗ Step {step_num} failed ({execution_time:.2f}s)")
                test_passed = False
                failed_steps.append(f"Step {step_num}: {step}")

                # Take screenshot of failure
                failure_screenshot = f"screenshots/failure_{test_id}_step{step_num}_{int(time.time())}.png"
                page.screenshot(path=failure_screenshot)
                print(f"Failure screenshot saved to: {failure_screenshot}")

                # Stop test case execution if a step fails
                break

        # Take screenshot after test
        screenshot_path = f"screenshots/after_{test_id}_{int(time.time())}.png"
        page.screenshot(path=screenshot_path)

        # Record test case result
        if test_passed:
            print(f"\n✓ Test case [{test_id}] {test_name} PASSED")
            results["passed"] += 1
        else:
            print(f"\n✗ Test case [{test_id}] {test_name} FAILED")
            results["failed"] += 1
            results["failures"].append({
                "test_id": test_id,
                "test_name": test_name,
                "failed_steps": failed_steps
            })

    # Print final results
    print(f"\n{'=' * 80}\nTest Execution Summary\n{'=' * 80}")
    print(f"Total test cases: {results['total']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Skipped: {results['skipped']}")

    if results["failures"]:
        print("\nFailed test cases:")
        for failure in results["failures"]:
            print(f"- [{failure['test_id']}] {failure['test_name']}")
            for step in failure["failed_steps"]:
                print(f"  * {step}")

    # Fail the test if any test case failed
    assert results["failed"] == 0, f"{results['failed']} test cases failed"



