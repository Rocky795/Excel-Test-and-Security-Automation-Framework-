# # File: page_actions.py
# import re
# import time
# from typing import Dict, Any, Union, Optional
# from playwright.sync_api import Page
# from object_repository import ObjectRepository


# class PageActions:
#     def __init__(self, page: Page, object_repository: ObjectRepository):
#         """Initialize PageActions with Playwright page and object repository"""
#         self.page = page
#         self.object_repository = object_repository

#     def execute_action(self, action_step: str, context: Optional[Dict[str, Any]] = None) -> bool:
#         """
#         Execute a test action based on the step description

#         Args:
#             action_step: The action to execute in natural language format
#             context: Optional context variables for dynamic data

#         Returns:
#             bool: True if action was successful, False otherwise
#         """
#         try:
#             # Initialize context if None
#             if context is None:
#                 context = {}

#             # Replace any variables in the action step
#             for var_name, var_value in context.items():
#                 action_step = action_step.replace(f"${{{var_name}}}", str(var_value))

#             # Parse the action from the beginning of the step
#             action_parts = action_step.strip().split(maxsplit=1)
#             if not action_parts:
#                 raise ValueError("Empty action step")

#             action = action_parts[0].lower()

#             # Get the remaining part of the step (after the action)
#             remaining = action_parts[1] if len(action_parts) > 1 else ""

#             # Execute the corresponding action method
#             if action == "click":
#                 return self._perform_click(remaining)
#             elif action == "fill":
#                 return self._perform_fill(remaining)
#             elif action == "select":
#                 return self._perform_select(remaining)
#             elif action == "verify":
#                 return self._perform_verification(remaining)
#             elif action == "wait":
#                 return self._perform_wait(remaining)
#             elif action == "navigate":
#                 return self._perform_navigate(remaining)
#             elif action == "screenshot":
#                 return self._take_screenshot(remaining)
#             elif action == "store":
#                 return self._store_value(remaining, context)
#             elif action == "hover":
#                 return self._perform_hover(remaining)
#             elif action == "press":
#                 return self._perform_keypress(remaining)
#             elif action == "check":
#                 return self._perform_check(remaining)
#             elif action == "uncheck":
#                 return self._perform_uncheck(remaining)
#             elif action == "refresh":
#                 return self._perform_refresh()
#             elif action == "execute":
#                 return self._execute_javascript(remaining)
#             else:
#                 raise ValueError(f"Unknown action: {action}")

#         except Exception as e:
#             print(f"Error executing action '{action_step}': {str(e)}")
#             return False

#     def _perform_click(self, object_description: str) -> bool:
#         """Click on an object"""
#         try:
#             locator = self.object_repository.get_object_locator(object_description)
#             self.page.click(locator)
#             print(f"Clicked on '{object_description}'")
#             return True
#         except Exception as e:
#             print(f"Failed to click on '{object_description}': {str(e)}")
#             return False

#     def _perform_fill(self, fill_description: str) -> bool:
#         """Fill a field with a value"""
#         try:
#             # Parse "fill [field] with [value]"
#             match = re.match(r"(.*?)\s+with\s+(.*)", fill_description)
#             if not match:
#                 raise ValueError(f"Invalid fill format. Expected 'fill [field] with [value]', got '{fill_description}'")

#             field_name = match.group(1).strip()
#             value = match.group(2).strip()

#             # Remove quotes if present
#             if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
#                 value = value[1:-1]

#             locator = self.object_repository.get_object_locator(field_name)
#             self.page.fill(locator, value)
#             print(f"Filled '{field_name}' with '{value}'")
#             return True
#         except Exception as e:
#             print(f"Failed to fill '{fill_description}': {str(e)}")
#             return False

#     def _perform_select(self, select_description: str) -> bool:
#         """Select an option from a dropdown"""
#         try:
#             # Parse "select [option] from [dropdown]"
#             match = re.match(r"(.*?)\s+from\s+(.*)", select_description)
#             if not match:
#                 raise ValueError(
#                     f"Invalid select format. Expected 'select [option] from [dropdown]', got '{select_description}'")

#             option = match.group(1).strip()
#             dropdown = match.group(2).strip()

#             # Remove quotes if present
#             if (option.startswith('"') and option.endswith('"')) or (option.startswith("'") and option.endswith("'")):
#                 option = option[1:-1]

#             locator = self.object_repository.get_object_locator(dropdown)

#             # Try different select strategies
#             try:
#                 # First try standard select element
#                 self.page.select_option(locator, label=option)
#             except Exception:
#                 # If that fails, try clicking the dropdown and then the option
#                 self.page.click(locator)

#                 # Wait a bit for dropdown to appear
#                 self.page.wait_for_timeout(500)

#                 # Try to find and click the option
#                 try:
#                     # Try by text
#                     self.page.click(f"text={option}")
#                 except Exception:
#                     # Try by xpath with contains
#                     self.page.click(f"//li[contains(text(), '{option}')]")

#             print(f"Selected '{option}' from '{dropdown}'")
#             return True
#         except Exception as e:
#             print(f"Failed to select '{select_description}': {str(e)}")
#             return False

#     def _perform_verification(self, verify_description: str) -> bool:
#         """Verify text or object state"""
#         try:
#             # Parse "verify [object/text] is [condition]"
#             match = re.match(r"(.*?)\s+is\s+(.*)", verify_description)
#             if not match:
#                 raise ValueError(
#                     f"Invalid verify format. Expected 'verify [object/text] is [condition]', got '{verify_description}'")

#             text_or_object = match.group(1).strip()
#             condition = match.group(2).strip()

#             # Try to get locator from repository, if not found use as plain text
#             try:
#                 locator = self.object_repository.get_object_locator(text_or_object)
#                 element = self.page.locator(locator)
#             except ValueError:
#                 # Not in repository, try as text
#                 if text_or_object.startswith('"') and text_or_object.endswith('"'):
#                     text_or_object = text_or_object[1:-1]
#                 element = self.page.locator(f"text={text_or_object}")

#             # Check different conditions
#             if condition == "visible":
#                 element.wait_for(state="visible", timeout=10000)
#                 print(f"Verified '{text_or_object}' is visible")
#             elif condition == "not visible" or condition == "invisible":
#                 element.wait_for(state="hidden", timeout=10000)
#                 print(f"Verified '{text_or_object}' is not visible")
#             elif condition == "enabled":
#                 assert element.is_enabled(), f"'{text_or_object}' is not enabled"
#                 print(f"Verified '{text_or_object}' is enabled")
#             elif condition == "disabled":
#                 assert not element.is_enabled(), f"'{text_or_object}' is not disabled"
#                 print(f"Verified '{text_or_object}' is disabled")
#             elif condition == "checked":
#                 assert element.is_checked(), f"'{text_or_object}' is not checked"
#                 print(f"Verified '{text_or_object}' is checked")
#             elif condition == "unchecked":
#                 assert not element.is_checked(), f"'{text_or_object}' is not unchecked"
#                 print(f"Verified '{text_or_object}' is unchecked")
#             elif condition=='available':
#                 element.wait_for(state="visible", timeout=10000)
#                 print(f"Verified '{text_or_object}' is available")
#             elif condition.startswith("containing"):
#                 text = condition[10:].strip()
#                 if text.startswith('"') and text.endswith('"'):
#                     text = text[1:-1]
#                 assert text in element.inner_text(), f"'{text_or_object}' does not contain '{text}'"
#                 print(f"Verified '{text_or_object}' contains '{text}'")
#             else:
#                 raise ValueError(f"Unknown condition: {condition}")

#             return True
#         except Exception as e:
#             print(f"Verification failed for '{verify_description}': {str(e)}")
#             return False

#     def _perform_wait(self, wait_description: str) -> bool:
#         """Wait for specified time or condition"""
#         try:
#             # Check if waiting for seconds or for an element
#             if wait_description.endswith("seconds") or wait_description.endswith("second"):
#                 # Wait for time
#                 seconds_str = wait_description.split()[0]
#                 seconds = int(seconds_str)
#                 self.page.wait_for_timeout(seconds * 1000)
#                 print(f"Waited for {seconds} seconds")
#             elif "for" in wait_description:
#                 # Wait for element
#                 match = re.match(r"for\s+(.*?)\s+to\s+be\s+(.*)", wait_description)
#                 if not match:
#                     raise ValueError(
#                         f"Invalid wait format. Expected 'wait for [element] to be [condition]', got '{wait_description}'")

#                 element_name = match.group(1).strip()
#                 condition = match.group(2).strip()

#                 locator = self.object_repository.get_object_locator(element_name)
#                 element = self.page.locator(locator)

#                 if condition == "visible":
#                     element.wait_for(state="visible", timeout=30000)
#                 elif condition == "invisible" or condition == "not visible":
#                     element.wait_for(state="hidden", timeout=30000)
#                 else:
#                     raise ValueError(f"Unknown wait condition: {condition}")

#                 print(f"Waited for '{element_name}' to be {condition}")
#             else:
#                 raise ValueError(f"Invalid wait format: {wait_description}")

#             return True
#         except Exception as e:
#             print(f"Wait failed for '{wait_description}': {str(e)}")
#             return False

#     def _perform_navigate(self, url: str) -> bool:
#         """Navigate to a URL"""
#         try:
#             # Remove quotes if present
#             if (url.startswith('"') and url.endswith('"')) or (url.startswith("'") and url.endswith("'")):
#                 url = url[1:-1]

#             # Check if it's a relative URL
#             if not url.startswith(('http://', 'https://')):
#                 # Assume it's relative to the current Salesforce instance
#                 current_url = self.page.url
#                 base_url = re.match(r'(https?://[^/]+)', current_url).group(1)
#                 url = f"{base_url}/{url.lstrip('/')}"

#             self.page.goto(url)
#             print(f"Navigated to {url}")
#             return True
#         except Exception as e:
#             print(f"Navigation failed to '{url}': {str(e)}")
#             return False

#     def _take_screenshot(self, description: str) -> bool:
#         """Take a screenshot"""
#         try:
#             # Create screenshots directory if it doesn't exist
#             import os
#             os.makedirs("screenshots", exist_ok=True)

#             # Generate filename from description or timestamp
#             if description:
#                 # Remove invalid characters from filename
#                 filename = re.sub(r'[^a-zA-Z0-9_-]', '_', description)
#             else:
#                 filename = f"screenshot_{int(time.time())}"

#             # Take screenshot
#             path = f"screenshots/{filename}.png"
#             self.page.screenshot(path=path)
#             print(f"Screenshot saved to {path}")
#             return True
#         except Exception as e:
#             print(f"Failed to take screenshot: {str(e)}")
#             return False

#     def _store_value(self, store_description: str, context: Dict[str, Any]) -> bool:
#         """Store a value in the context"""
#         try:
#             # Parse "store [value/text from element] as [variable_name]"
#             match = re.match(r"(.*?)\s+as\s+(.*)", store_description)
#             if not match:
#                 raise ValueError(
#                     f"Invalid store format. Expected 'store [value] as [variable]', got '{store_description}'")

#             value_expr = match.group(1).strip()
#             variable_name = match.group(2).strip()

#             # Check if we're storing from an element
#             if "text from" in value_expr:
#                 element_name = value_expr.replace("text from", "").strip()
#                 locator = self.object_repository.get_object_locator(element_name)
#                 value = self.page.locator(locator).inner_text()
#             elif "value from" in value_expr:
#                 element_name = value_expr.replace("value from", "").strip()
#                 locator = self.object_repository.get_object_locator(element_name)
#                 value = self.page.locator(locator).input_value()
#             else:
#                 # Store a literal value
#                 value = value_expr
#                 # Remove quotes if present
#                 if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
#                     value = value[1:-1]

#             # Store in context
#             context[variable_name] = value
#             print(f"Stored '{value}' as '{variable_name}'")
#             return True
#         except Exception as e:
#             print(f"Failed to store value from '{store_description}': {str(e)}")
#             return False

#     def _perform_hover(self, object_description: str) -> bool:
#         """Hover over an object"""
#         try:
#             locator = self.object_repository.get_object_locator(object_description)
#             self.page.hover(locator)
#             print(f"Hovered over '{object_description}'")
#             return True
#         except Exception as e:
#             print(f"Failed to hover over '{object_description}': {str(e)}")
#             return False

#     def _perform_keypress(self, key_description: str) -> bool:
#         """Press a key or key combination"""
#         try:
#             # Check if it's for a specific element
#             if " in " in key_description:
#                 # Format: "press [key] in [element]"
#                 parts = key_description.split(" in ")
#                 key = parts[0].strip()
#                 element = parts[1].strip()

#                 locator = self.object_repository.get_object_locator(element)
#                 self.page.press(locator, key)
#                 print(f"Pressed '{key}' in '{element}'")
#             else:
#                 # Press key globally
#                 if key_description.lower() == "enter":
#                     # Special case for Enter key (can be sent globally)
#                     self.page.keyboard.press("Enter")
#                     print(f"Pressed 'Enter' key globally")
#                 else:
#                     self.page.keyboard.press(key_description)
#                     print(f"Pressed '{key_description}'")

#             return True
#         except Exception as e:
#             print(f"Failed to press '{key_description}': {str(e)}")
#             return False

#     def _perform_check(self, object_description: str) -> bool:
#         """Check a checkbox"""
#         try:
#             locator = self.object_repository.get_object_locator(object_description)
#             self.page.check(locator)
#             print(f"Checked '{object_description}'")
#             return True
#         except Exception as e:
#             print(f"Failed to check '{object_description}': {str(e)}")
#             return False

#     def _perform_uncheck(self, object_description: str) -> bool:
#         """Uncheck a checkbox"""
#         try:
#             locator = self.object_repository.get_object_locator(object_description)
#             self.page.uncheck(locator)
#             print(f"Unchecked '{object_description}'")
#             return True
#         except Exception as e:
#             print(f"Failed to uncheck '{object_description}': {str(e)}")
#             return False

#     def _perform_refresh(self) -> bool:
#         """Refresh the current page"""
#         try:
#             self.page.reload()
#             print("Page refreshed")
#             return True
#         except Exception as e:
#             print(f"Failed to refresh page: {str(e)}")
#             return False

#     def _execute_javascript(self, js_code: str) -> bool:
#         """Execute JavaScript code"""
#         try:
#             # Remove quotes if present
#             if (js_code.startswith('"') and js_code.endswith('"')) or (
#                     js_code.startswith("'") and js_code.endswith("'")):
#                 js_code = js_code[1:-1]

#             result = self.page.evaluate(js_code)
#             print(f"Executed JavaScript. Result: {result}")
#             return True
#         except Exception as e:
#             print(f"Failed to execute JavaScript '{js_code}': {str(e)}")
#             return False

