import logging
from pathlib import Path
from typing import List, Dict, Any
import json
import os
from datetime import datetime


class GenerateReport:
    def __init__(self, results, results_dir, timestamp, logger=None):
        self.results = results
        self.results_dir = results_dir
        self.timestamp = timestamp
        self.logger = logger or logging.getLogger("SalesforceAutomation")
    
    def generate_report(self):
        """Generate HTML and JSON reports from test results"""
        results = self.results  # instance variable
        results_dir = self.results_dir
        total = len(results)
        passed = sum(1 for r in results if r["status"] == "PASSED")
        failed = sum(1 for r in results if r["status"] == "FAILED")
        errors = sum(1 for r in results if r["status"] == "ERROR")
        
        # Create JSON report
        json_report = {
            "summary": {
                "timestamp": self.timestamp,
                "total": total,
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "success_rate": f"{(passed/total)*100:.2f}%" if total > 0 else "0%"
            },
            "test_cases": results
        }
        
        json_report_path = os.path.join(results_dir, "test_results.json")
        with open(json_report_path, 'w') as f:
            json.dump(json_report, f, indent=4)
        
        # Create HTML report
        html_report_path = os.path.join(results_dir, "test_report.html")
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Salesforce Automation Test Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .header {{ background-color: #0288d1; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                .summary {{ display: flex; justify-content: space-between; margin-bottom: 20px; }}
                .summary-card {{ background-color: white; border-radius: 5px; padding: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); flex: 1; margin: 0 10px; text-align: center; }}
                .passed {{ color: #4caf50; }}
                .failed {{ color: #f44336; }}
                .error {{ color: #ff9800; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f5f5f5; }}
                tr:hover {{ background-color: #f5f5f5; }}
                .status-badge {{ padding: 5px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; }}
                .details-btn {{ padding: 5px 10px; background-color: #0288d1; color: white; border: none; border-radius: 4px; cursor: pointer; }}
                .test-details {{ display: none; padding: 10px; background-color: #f9f9f9; border-radius: 4px; margin-top: 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Salesforce Automation Test Report</h1>
                    <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                </div>
                
                <div class="summary">
                    <div class="summary-card">
                        <h2>Total Tests</h2>
                        <p style="font-size: 24px;">{total}</p>
                    </div>
                    <div class="summary-card">
                        <h2>Passed</h2>
                        <p class="passed" style="font-size: 24px;">{passed}</p>
                    </div>
                    <div class="summary-card">
                        <h2>Failed</h2>
                        <p class="failed" style="font-size: 24px;">{failed}</p>
                    </div>
                    <div class="summary-card">
                        <h2>Errors</h2>
                        <p class="error" style="font-size: 24px;">{errors}</p>
                    </div>
                    <div class="summary-card">
                        <h2>Success Rate</h2>
                        <p style="font-size: 24px;">{(passed/total)*100:.2f}%</p>
                    </div>
                </div>
                
                <table>
                    <thead>
                        <tr>
                            <th>Test ID</th>
                            <th>Test Name</th>
                            <th>Status</th>
                            <th>Execution Time</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        for result in results:
            self.logger.info(f"Result data: {result}")
            status_class = "passed" if result["status"] == "PASSED" else ("failed" if result["status"] == "FAILED" else "error")
            
            execution_time = result.get("execution_time", "N/A")
            if isinstance(execution_time, (int, float)):
                execution_time = f"{execution_time:.2f}s"
            
            html_content += f"""
                <tr>
                    <td>{result["test_id"]}</td>
                    <td>{result["test_name"]}</td>
                    <td><span class="status-badge {status_class}">{result["status"]}</span></td>
                    <td>{execution_time}</td>
                    <td><button onclick="toggleDetails('{result["test_id"]}')" class="details-btn">Details</button></td>
                </tr>
                <tr>
                    <td colspan="5">
                        <div id="{result["test_id"]}_details" class="test-details">
            """
            
            if result["status"] == "FAILED" and "failed_steps" in result:
                html_content += "<h4>Failed Steps:</h4><ul>"
                for step in result["failed_steps"]:
                    html_content += f"<li>{step}</li>"
                html_content += "</ul>"
            
            if "error" in result:
                html_content += f"<h4>Error:</h4><p>{result['error']}</p>"
            
            # Link for log file using a proper file URI:
            if "log_file" in result:
                log_uri = Path(result["log_file"]).resolve().as_uri()
                html_content += f'<p><a href="{log_uri}" target="_blank">View Log File</a></p>'
            
            # Link for screenshot if available:
            if "screenshot_path" in result:
                screenshot_uri = Path(result["screenshot_path"]).resolve().as_uri()
                html_content += f'<p><a href="{screenshot_uri}" target="_blank">View Screenshot</a></p>'
            
            # Link for video if available:
            if "video_path" in result:
                video_uri = Path(result["video_path"]).resolve().as_uri()
                html_content += f'<p><a href="{video_uri}" target="_blank">View Video</a></p>'
            
            html_content += """
                        </div>
                    </td>
                </tr>
            """
        
        html_content += """
                    </tbody>
                </table>
            </div>
            
            <script>
                function toggleDetails(testId) {
                    const detailsElement = document.getElementById(testId + '_details');
                    if (detailsElement.style.display === 'block') {
                        detailsElement.style.display = 'none';
                    } else {
                        detailsElement.style.display = 'block';
                    }
                }
            </script>
        </body>
        </html>
        """
        
        with open(html_report_path, 'w') as f:
            f.write(html_content)
        
        self.logger.info(f"Generated JSON report: {json_report_path}")
        self.logger.info(f"Generated HTML report: {html_report_path}")
        
        return html_report_path, json_report_path
