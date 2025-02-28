import pytest
import os
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Add additional browser context options like viewport size"""
    return {
        **browser_context_args,
        "viewport": {
            "width": 1920,
            "height": 1080,
        },
        "record_video_dir": "videos/",
    }


@pytest.fixture(scope="session")
def playwright():
    with sync_playwright() as playwright:
        yield playwright


@pytest.fixture(scope="session")
def browser(playwright):
    browser = playwright.chromium.launch(headless=False, slow_mo=100)
    yield browser
    browser.close()


@pytest.fixture(scope="function")
def page(browser):
    context = browser.new_context(
        record_video_dir="videos/",
        ignore_https_errors=True
    )
    page = context.new_page()

    # Setup page for Salesforce logging
    page.on("console", lambda msg: print(f"Browser console: {msg.text}"))

    yield page

    # Cleanup
    context.close()


@pytest.fixture(scope="function")
def salesforce_login(page):
    """Login to Salesforce"""
    page.goto(os.getenv("SALESFORCE_URL", "https://login.salesforce.com/"))

    page.fill("xpath=//input[@name='username']", os.getenv("SALESFORCE_USERNAME", ""))
    page.fill("xpath=//input[@name='pw']", os.getenv("SALESFORCE_PASSWORD", ""))
    page.click("#Login")

    # Wait for Salesforce to load
    page.wait_for_selector("xpath=//button[@title='App Launcher']", state="visible", timeout=60000)

    yield page