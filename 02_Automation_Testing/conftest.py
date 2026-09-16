import configparser
import os
from datetime import datetime

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

BASE_DIR = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(BASE_DIR, "config", "config.ini")
SCREENSHOTS_DIR = os.path.join(BASE_DIR, "screenshots")


@pytest.fixture(scope="session")
def config():
    parser = configparser.ConfigParser()
    parser.read(CONFIG_PATH)
    return parser


@pytest.fixture
def driver(config):
    options = Options()
    if config.getboolean("browser", "headless"):
        options.add_argument("--headless=new")
    # the app switches to a compact mobile layout on narrow viewports,
    # maximizing keeps it on the desktop layout our page objects target
    options.add_argument("--start-maximized")

    chrome_driver = webdriver.Chrome(options=options)
    chrome_driver.get(config["app"]["base_url"])

    yield chrome_driver

    chrome_driver.quit()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        chrome_driver = item.funcargs.get("driver")
        if chrome_driver is not None:
            os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(SCREENSHOTS_DIR, f"{item.name}_{timestamp}.png")
            chrome_driver.save_screenshot(screenshot_path)
            print(f"\nScreenshot saved: {screenshot_path}")
