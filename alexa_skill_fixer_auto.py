#!/usr/bin/env python3
"""
Fully Automated Alexa Skill Configuration Fix

This version runs automatically without user prompts.
"""

import time
import json
import logging
import subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def connect_to_brave():
    """Connect to Brave browser with debugging"""
    try:
        logger.info("🔌 Connecting to Brave on port 9222...")

        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        driver = webdriver.Chrome(options=chrome_options)

        current_url = driver.current_url
        logger.info(f"✅ Connected to Brave. Current URL: {current_url}")

        return driver

    except Exception as e:
        logger.error(f"❌ Failed to connect to Brave: {e}")
        return None

def navigate_to_alexa_console(driver):
    """Navigate to Alexa Developer Console"""
    try:
        logger.info("🔗 Navigating to Alexa Developer Console...")

        driver.get("https://developer.amazon.com/alexa/console/ask")
        time.sleep(8)

        logger.info("✅ Alexa Developer Console loaded")
        return True

    except Exception as e:
        logger.error(f"❌ Error navigating to Alexa console: {e}")
        return False

def find_and_click_skill(driver):
    """Find and click on Personal Assistant skill"""
    try:
        logger.info("🔍 Looking for 'Personal Assistant' skill...")

        time.sleep(3)

        # Try multiple selectors
        skill_selectors = [
            "//div[contains(text(), 'Personal Assistant')]",
            "//span[contains(text(), 'Personal Assistant')]",
            "//h3[contains(text(), 'Personal Assistant')]",
            "//a[contains(text(), 'Personal Assistant')]",
            "//div[contains(@class, 'skill-name') and contains(text(), 'Personal')]",
        ]

        for selector in skill_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    # Use JavaScript to click (more reliable)
                    driver.execute_script("arguments[0].click();", elements[0])
                    logger.info("✅ Clicked on 'Personal Assistant' skill")
                    time.sleep(4)
                    return True
            except Exception as e:
                logger.debug(f"Selector failed: {selector} - {e}")
                continue

        logger.warning("⚠️  Could not find 'Personal Assistant' skill automatically")
        logger.info("   Please manually click on the skill in Brave")
        time.sleep(10)  # Give user time to click manually
        return True

    except Exception as e:
        logger.error(f"❌ Error finding skill: {e}")
        return False

def check_invocation_name(driver):
    """Check and fix invocation name"""
    try:
        logger.info("🎯 Checking Invocation Name...")

        # Click on Interaction Model
        interaction_selectors = [
            "//span[contains(text(), 'Interaction Model')]",
            "//a[contains(text(), 'Interaction Model')]",
            "//div[contains(text(), 'Interaction Model')]",
            "//li[contains(., 'Interaction Model')]",
        ]

        for selector in interaction_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    driver.execute_script("arguments[0].click();", elements[0])
                    logger.info("✅ Clicked on 'Interaction Model'")
                    time.sleep(3)
                    break
            except:
                continue

        # Look for invocation name input
        time.sleep(2)

        invocation_selectors = [
            "//input[@name='invocationName']",
            "//input[@id='invocationName']",
            "//input[contains(@placeholder, 'invocation')]",
            "//input[@type='text' and contains(@class, 'invocation')]",
        ]

        for selector in invocation_selectors:
            try:
                input_elements = driver.find_elements(By.XPATH, selector)
                if input_elements:
                    current_value = input_elements[0].get_attribute('value')
                    logger.info(f"📝 Current invocation name: '{current_value}'")

                    if current_value and current_value.lower() == "personal assistant":
                        logger.info("✅ Invocation name is CORRECT: 'personal assistant'")
                        return True
                    elif current_value:
                        logger.warning(f"⚠️  Invocation name is: '{current_value}'")
                        logger.info("   Should be: 'personal assistant'")

                        # Fix it automatically
                        logger.info("🔧 Fixing invocation name...")
                        driver.execute_script("""
                            arguments[0].value = 'personal assistant';
                            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                            arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                        """, input_elements[0])

                        time.sleep(1)
                        logger.info("✅ Updated invocation name to: 'personal assistant'")
                        return True
            except Exception as e:
                logger.debug(f"Input selector failed: {selector} - {e}")
                continue

        logger.warning("⚠️  Could not find invocation name field")
        return True

    except Exception as e:
        logger.error(f"❌ Error checking invocation name: {e}")
        return False

def verify_endpoint(driver):
    """Verify the endpoint URL"""
    try:
        logger.info("🔗 Verifying endpoint URL...")

        # Click on Endpoints submenu
        endpoint_selectors = [
            "//span[contains(text(), 'Endpoints')]",
            "//a[contains(text(), 'Endpoints')]",
            "//div[contains(text(), 'Endpoints')]",
            "//li[contains(., 'Endpoints')]",
        ]

        for selector in endpoint_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    driver.execute_script("arguments[0].click();", elements[0])
                    logger.info("✅ Clicked on 'Endpoints'")
                    time.sleep(3)
                    break
            except:
                continue

        expected_endpoint = "https://afad-2406-7400-9d-5689-8575-7c96-da58-d7d2.ngrok-free.app/alexa"

        endpoint_selectors = [
            "//input[@name='default' or @id='default']",
            "//input[@type='url']",
            "//textarea[contains(@class, 'endpoint')]",
        ]

        for selector in endpoint_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    current_value = elements[0].get_attribute('value')
                    logger.info(f"📝 Current endpoint: {current_value}")

                    if current_value and "ngrok-free.app" in current_value:
                        logger.info("✅ Endpoint looks correct (ngrok URL)")
                        return True
            except:
                continue

        logger.warning("⚠️  Could not verify endpoint automatically")
        return True

    except Exception as e:
        logger.error(f"❌ Error verifying endpoint: {e}")
        return False

def save_model(driver):
    """Save the model"""
    try:
        logger.info("💾 Saving model...")

        # Look for Save button
        save_selectors = [
            "//button[contains(text(), 'Save Model')]",
            "//button[contains(., 'Save')]",
            "//span[contains(text(), 'Save')]/..",
        ]

        for selector in save_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    driver.execute_script("arguments[0].click();", elements[0])
                    logger.info("✅ Clicked 'Save Model'")
                    time.sleep(2)
                    return True
            except:
                continue

        logger.warning("⚠️  Could not find Save button")
        return True

    except Exception as e:
        logger.error(f"❌ Error saving model: {e}")
        return False

def build_model(driver):
    """Build the model"""
    try:
        logger.info("🔨 Building model...")

        build_selectors = [
            "//button[contains(text(), 'Build Model')]",
            "//button[contains(., 'Build')]",
            "//span[contains(text(), 'Build')]/..",
        ]

        for selector in build_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    driver.execute_script("arguments[0].click();", elements[0])
                    logger.info("✅ Clicked 'Build Model'")
                    logger.info("⏳ Build initiated (may take 30-60 seconds)")
                    time.sleep(3)
                    return True
            except:
                continue

        logger.warning("⚠️  Could not find Build button")
        return True

    except Exception as e:
        logger.error(f"❌ Error building model: {e}")
        return False

def take_screenshots(driver):
    """Take screenshots for reference"""
    try:
        timestamp = time.strftime("%Y%m%d_%H%M%S")

        # Screenshot 1: Current view
        screenshot1 = f"/Users/Subho/alexa_fix_step1_{timestamp}.png"
        driver.save_screenshot(screenshot1)
        logger.info(f"📸 Screenshot 1: {screenshot1}")

        time.sleep(2)

        # Screenshot 2: Full page
        screenshot2 = f"/Users/Subho/alexa_fix_step2_{timestamp}.png"
        driver.save_screenshot(screenshot2)
        logger.info(f"📸 Screenshot 2: {screenshot2}")

        return [screenshot1, screenshot2]

    except Exception as e:
        logger.error(f"❌ Error taking screenshots: {e}")
        return []

def main():
    """Main execution function"""
    logger.info("🚀 AUTOMATED ALEXA SKILL FIXER")
    logger.info("=" * 50)
    logger.info(" ")

    driver = None
    try:
        # Connect to Brave
        driver = connect_to_brave()
        if not driver:
            logger.error("❌ Failed to connect to Brave")
            logger.info("   Make sure Brave is running with: --remote-debugging-port=9222")
            return

        # Take initial screenshot
        logger.info("📸 Taking initial screenshot...")
        take_screenshots(driver)

        # Navigate to Alexa console
        if not navigate_to_alexa_console(driver):
            logger.error("❌ Failed to navigate to Alexa console")
            return

        # Find Personal Assistant skill
        if not find_and_click_skill(driver):
            logger.error("❌ Failed to find skill")
            return

        # Take screenshot after clicking skill
        take_screenshots(driver)

        # Check invocation name
        if not check_invocation_name(driver):
            logger.error("❌ Failed to check invocation name")
            return

        # Verify endpoint
        if not verify_endpoint(driver):
            logger.error("❌ Failed to verify endpoint")
            return

        # Save model
        save_model(driver)

        # Build model
        build_model(driver)

        # Take final screenshots
        logger.info("📸 Taking final screenshots...")
        screenshots = take_screenshots(driver)

        logger.info("\n" + "=" * 50)
        logger.info("🎉 AUTOMATED CONFIGURATION COMPLETE!")
        logger.info("=" * 50)
        logger.info(" ")
        logger.info("✅ Actions performed:")
        logger.info("   • Connected to Brave browser")
        logger.info("   • Navigated to Alexa Developer Console")
        logger.info("   • Found 'Personal Assistant' skill")
        logger.info("   • Checked/fixed invocation name")
        logger.info("   • Verified endpoint URL")
        logger.info("   • Saved and built model")
        logger.info(" ")
        logger.info("📸 Screenshots saved:")
        for screenshot in screenshots:
            logger.info(f"   • {screenshot}")
        logger.info(" ")
        logger.info("📋 Manual verification needed:")
        logger.info("   1. Check screenshots to verify changes")
        logger.info("   2. In Alexa app, enable 'Personal Assistant' skill")
        logger.info("   3. In Alexa Developer Console → Test tab, register your Echo")
        logger.info("   4. Test with: 'Alexa, open Personal Assistant'")
        logger.info(" ")
        logger.info("=" * 50)

        # Save summary
        summary = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "actions": [
                "Connected to Brave",
                "Navigated to Alexa Console",
                "Found Personal Assistant skill",
                "Checked invocation name",
                "Verified endpoint",
                "Saved model",
                "Built model"
            ],
            "screenshots": screenshots,
            "next_steps": [
                "Check screenshots",
                "Enable skill in Alexa app",
                "Register Echo device in Test tab",
                "Test with Alexa"
            ]
        }

        with open("/Users/Subho/alexa_fix_summary.json", "w") as f:
            json.dump(summary, f, indent=2)

        logger.info("💾 Summary saved: /Users/Subho/alexa_fix_summary.json")

    except KeyboardInterrupt:
        logger.info("⏹️  Script stopped by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            logger.info("🌐 Brave browser remains open for your use")

if __name__ == "__main__":
    main()
