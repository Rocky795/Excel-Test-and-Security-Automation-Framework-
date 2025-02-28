# import time
#
# from playwright.sync_api import Playwright, sync_playwright
#
#
#
# def run(playwright: Playwright) -> None:
#     browser = playwright.chromium.launch(headless=False)
#     context = browser.new_context()
#     page = context.new_page()
#
#     page.goto(
#         "https://resourceful-wolf-dzqax0-dev-ed.trailblaze.my.salesforce.com/?ec=302&startURL=%2Fvisualforce%2Fsession%3Furl%3Dhttps%253A%252F%252Fresourceful-wolf-dzqax0-dev-ed.trailblaze.lightning.force.com%252Flightning%252Fpage%252Fhome")
#
#     # Login
#     # page.get_by_role("textbox", name="Username").fill("test@unisys.com")
#     page.locator(("xpath=//input[@name='username']")).fill("test@unisys.com")
#     page.get_by_role("textbox", name="Username").press("Tab")
#
#     page.get_by_role("textbox", name="Password").fill("Pass@123")
#     page.get_by_role("textbox", name="Password").press("Enter")
#
#     page.locator("xpath=//button[@title='App Launcher']").click()
#
#     # Further interactions after the App Launcher button click
#     page.get_by_role("combobox", name="Search apps and items...").click()
#     page.get_by_role("combobox", name="Search apps and items...").fill("Sales")
#     page.get_by_role("option", name="Sales", exact=True).click()
#     time.sleep(0.5)
#     page.locator("xpath=//a[@title='Opportunities']").wait_for()
#     page.locator("xpath=//a[@title='Opportunities']").click()
#     page.locator("xpath=//span[text()='Recently Viewed' and @data-aura-class='uiOutputText']").wait_for(state="visible")
#     page.locator("xpath=//span[text()='Recently Viewed' and @data-aura-class='uiOutputText']").click(force=True)
#     # page.get_by_role("button", name="Select a List View:").click()
#     page.locator("xpath=(//a[.//span[text()='All Opportunities']])[1]").wait_for(state="visible")
#     page.locator("xpath=(//a[.//span[text()='All Opportunities']])[1]").click()
#
#     page.get_by_role("button", name="New").click()
#     page.get_by_role("textbox", name="Amount").fill("")
#     page.get_by_role("textbox", name="*Opportunity Name").click()
#     page.get_by_role("textbox", name="*Opportunity Name").fill("One")
#     page.get_by_role("textbox", name="*Close Date").click()
#     page.get_by_label("-02-28").get_by_role("button", name="28").click()
#     page.get_by_role("combobox", name="Stage").click()
#     page.get_by_title("Qualification", exact=True).click()
#     page.get_by_role("button", name="Save", exact=True).click()
#
#     # Close context and browser
#     context.close()
#     browser.close()
#
# with sync_playwright() as playwright:
#     run(playwright)
