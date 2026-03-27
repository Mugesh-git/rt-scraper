# ─────────────────────────────────────────────
#  scraper/loader.py
#  Selenium driver + "Load More" pagination
# ─────────────────────────────────────────────

import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, ElementClickInterceptedException
)
from bs4 import BeautifulSoup
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config

log = logging.getLogger(__name__)


def _build_driver() -> webdriver.Chrome:
    """Build and return a configured Chrome WebDriver."""
    opts = Options()
    if config.HEADLESS:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument(f"user-agent={config.HEADERS['User-Agent']}")
    opts.add_argument("--log-level=3")
    opts.add_experimental_option("excludeSwitches", ["enable-logging"])

    try:
        from selenium.webdriver.chrome.service import Service as ChromeService
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            service = ChromeService(ChromeDriverManager().install())
        except Exception:
            service = ChromeService()
        driver = webdriver.Chrome(service=service, options=opts)
    except Exception as e:
        log.error(f"Could not start Chrome driver: {e}")
        raise

    driver.set_page_load_timeout(config.PAGE_LOAD_TIMEOUT)
    driver.implicitly_wait(config.IMPLICIT_WAIT)
    return driver


# ── Load-More selectors (try them in order) ─────────────────────────────────
_LOAD_MORE_SELECTORS = [
    "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'load more')]",
    "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'show more')]",
    "//*[@data-qa='discovery-tiles-load-more']",
    "//button[contains(@class,'load-more')]",
    "//button[contains(@class,'show-more')]",
    "//*[contains(@class,'load-more')]//button",
]


def _count_movies(driver) -> int:
    """Count visible movie containers currently loaded on page."""
    containers = driver.find_elements(By.CSS_SELECTOR, "div.flex-container")
    if not containers:
        containers = driver.find_elements(By.CSS_SELECTOR, "[data-qa='discovery-media-list-item']")
    return len(containers)


def _click_load_more(driver) -> bool:
    """
    Try to find and click the 'Load More' button.
    Returns True if clicked successfully, False if not found.
    """
    for xpath in _LOAD_MORE_SELECTORS:
        try:
            btn = WebDriverWait(driver, 4).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            time.sleep(0.4)
            try:
                btn.click()
            except ElementClickInterceptedException:
                driver.execute_script("arguments[0].click();", btn)
            log.info("  ✓ Clicked 'Load More'")
            return True
        except (TimeoutException, NoSuchElementException):
            continue
    return False


def fetch_page_with_target(url: str, target_count: int) -> BeautifulSoup:
    """
    Open `url` in Selenium, keep clicking 'Load More' until
    at least `target_count` movies are visible (or no more button exists).
    Returns a BeautifulSoup of the final page source.
    """
    log.info(f"Opening browser → {url}")
    driver = _build_driver()

    try:
        driver.get(url)
        time.sleep(2)  # initial render

        current = _count_movies(driver)
        log.info(f"  Initial movies loaded: {current}")

        if current >= target_count:
            log.info("  Target reached without needing 'Load More'.")
        else:
            attempts = 0
            max_attempts = 50  # safety cap
            while current < target_count and attempts < max_attempts:
                clicked = _click_load_more(driver)
                if not clicked:
                    log.info("  No 'Load More' button found — reached end of list.")
                    break
                time.sleep(config.LOAD_MORE_WAIT)
                new_count = _count_movies(driver)
                if new_count == current:
                    log.warning("  Count didn't increase after click — stopping.")
                    break
                current = new_count
                log.info(f"  Movies now loaded: {current} / {target_count}")
                attempts += 1

        log.info(f"  Final movie count on page: {current}")
        soup = BeautifulSoup(driver.page_source, "html.parser")
        return soup

    finally:
        driver.quit()
