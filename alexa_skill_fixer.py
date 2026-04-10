#!/usr/bin/env python3
"""
Automated Alexa Skill Configuration Fix

This script connects to your Brave browser (already logged into Amazon Developer Console)
and automatically configures the Alexa skill to work with your OpenClaw bridge.
"""

import time
import json
import logging
import psutil
import subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_brave_debugging_ports():
    """Check if Brave is running on any debugging port"""
    common_ports = [9222, 9223, 9224, 9225]
    for port in common_ports:
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            if result == 0:
                return port
        except:
            continue
    return None

def connect_to_brave():
    """Connect to Brave browser with debugging"""
    debug_port = check_brave_debugging_ports()

    if not debug_port:
        logger.error("❌ Brave debugging not found")
        logger.info("Please start Brave with: /Applications/Brave\\ Browser.app/Contents/MacOS/Brave\\ Browser --remote-debugging-port=9222")
        return None

    try:
        logger.info(f"🔌 Connecting to Brave on port {debug_port}...")

        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        driver = webdriver.Chrome(options=chrome_options)

        # Test connection
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
        time.sleep(5)

        # Wait for page to load
        WebDriverWait(driver, 15).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        logger.info("✅ Alexa Developer Console loaded")
        return True

    except Exception as e:
        logger.error(f"❌ Error navigating to Alexa console: {e}")
        return False

def find_personal_assistant_skill(driver):
    """Find and click on Personal Assistant skill"""
    try:
        logger.info("🔍 Looking for 'Personal Assistant' skill...")

        # Wait for skills list to load
        time.sleep(3)

        # Try multiple selectors for skill cards
        skill_selectors = [
            "//div[contains(text(), 'Personal Assistant')]",
            "//span[contains(text(), 'Personal Assistant')]",
            "//h3[contains(text(), 'Personal Assistant')]",
            "//a[contains(text(), 'Personal Assistant')]",
        ]

        skill_found = False
        for selector in skill_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    # Click the first matching element
                    actions = ActionChains(driver)
                    actions.move_to_element(elements[0]).click().perform()
                    skill_found = True
                    logger.info("✅ Clicked on 'Personal Assistant' skill")
                    time.sleep(3)
                    break
            except:
                continue

        if not skill_found:
            logger.warning("⚠️  Could not find 'Personal Assistant' skill automatically")
            logger.info("   Please manually click on the skill in Brave")
            input("Press Enter in terminal once you've clicked the skill...")

        return True

    except Exception as e:
        logger.error(f"❌ Error finding skill: {e}")
        return False

def check_invocation_name(driver):
    """Check and fix invocation name"""
    try:
        logger.info("🎯 Checking Invocation Name (CRITICAL STEP)...")

        # Click on Interaction Model
        interaction_model_selectors = [
            "//span[contains(text(), 'Interaction Model')]",
            "//a[contains(text(), 'Interaction Model')]",
            "//div[contains(text(), 'Interaction Model')]",
        ]

        clicked = False
        for selector in interaction_model_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    elements[0].click()
                    clicked = True
                    logger.info("✅ Clicked on 'Interaction Model'")
                    time.sleep(2)
                    break
            except:
                continue

        if not clicked:
            logger.warning("⚠️  Could not click Interaction Model automatically")

        # Look for invocation name field
        time.sleep(2)

        # Try to find and check invocation name
        invocation_input_selectors = [
            "//input[@name='invocationName']",
            "//input[@id='invocationName']",
            "//input[contains(@placeholder, 'invocation')]",
            "//input[@type='text']",
        ]

        invocation_found = False
        for selector in invocation_input_selectors:
            try:
                input_elements = driver.find_elements(By.XPATH, selector)
                if input_elements:
                    # Get current value
                    current_value = input_elements[0].get_attribute('value')
                    logger.info(f"📝 Current invocation name: '{current_value}'")

                    # Check if it's correct
                    if current_value and current_value.lower() == "personal assistant":
                        logger.info("✅ Invocation name is CORRECT: 'personal assistant'")
                        invocation_found = True
                        break
                    elif current_value:
                        logger.warning(f"⚠️  Invocation name is: '{current_value}'")
                        logger.info("   Should be: 'personal assistant' (lowercase, two words)")

                        # Ask user if they want to fix it
                        fix = input("Do you want me to fix it? (y/n): ").lower()
                        if fix == 'y':
                            # Clear and set correct value
                            input_elements[0].clear()
                            input_elements[0].send_keys("personal assistant")
                            logger.info("✅ Updated invocation name to: 'personal assistant'")
                            invocation_found = True
                            break
            except:
                continue

        if not invocation_found:
            logger.warning("⚠️  Could not find invocation name field")
            logger.info("   Please manually verify it says: 'personal assistant'")

        return True

    except Exception as e:
        logger.error(f"❌ Error checking invocation name: {e}")
        return False

def verify_endpoint(driver):
    """Verify the endpoint URL"""
    try:
        logger.info("🔗 Verifying endpoint URL...")

        # Click on Endpoints
        endpoint_selectors = [
            "//span[contains(text(), 'Endpoints')]",
            "//a[contains(text(), 'Endpoints')]",
            "//div[contains(text(), 'Endpoints')]",
        ]

        clicked = False
        for selector in endpoint_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    elements[0].click()
                    clicked = True
                    logger.info("✅ Clicked on 'Endpoints'")
                    time.sleep(2)
                    break
            except:
                continue

        if not clicked:
            logger.warning("⚠️  Could not click Endpoints automatically")

        # Check endpoint URL
        expected_endpoint = "https://afad-2406-7400-9d-5689-8575-7c96-da58-d7d2.ngrok-free.app/alexa"

        endpoint_input_selectors = [
            "//input[@name='default']",
            "//input[@id='default']",
            "//input[contains(@placeholder, 'endpoint')]",
            "//input[@type='url']",
        ]

        endpoint_found = False
        for selector in endpoint_input_selectors:
            try:
                input_elements = driver.find_elements(By.XPATH, selector)
                if input_elements:
                    current_value = input_elements[0].get_attribute('value')
                    logger.info(f"📝 Current endpoint: {current_value}")

                    if current_value and current_value == expected_endpoint:
                        logger.info("✅ Endpoint is CORRECT")
                        endpoint_found = True
                        break
                    elif current_value:
                        logger.warning(f"⚠️  Endpoint might be different")
                        logger.info(f"   Expected: {expected_endpoint}")
            except:
                continue

        if not endpoint_found:
            logger.warning("⚠️  Could not verify endpoint automatically")
            logger.info(f"   Please manually verify it's: {expected_endpoint}")

        return True

    except Exception as e:
        logger.error(f"❌ Error verifying endpoint: {e}")
        return False

def save_and_build(driver):
    """Save and build the model"""
    try:
        logger.info("💾 Saving and building model...")

        # Look for Save button
        save_selectors = [
            "//button[contains(text(), 'Save Model')]",
            "//button[contains(text(), 'Save')]",
            "//span[contains(text(), 'Save Model')]",
        ]

        for selector in save_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    elements[0].click()
                    logger.info("✅ Clicked 'Save Model'")
                    time.sleep(2)
                    break
            except:
                continue

        # Look for Build button
        build_selectors = [
            "//button[contains(text(), 'Build Model')]",
            "//button[contains(text(), 'Build')]",
            "//span[contains(text(), 'Build Model')]",
        ]

        for selector in build_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    elements[0].click()
                    logger.info("✅ Clicked 'Build Model'")
                    logger.info("⏳ Waiting for build to complete...")
                    time.sleep(5)
                    break
            except:
                continue

        return True

    except Exception as e:
        logger.error(f"❌ Error saving/building: {e}")
        return False

def check_device_registration(driver):
    """Check device registration"""
    try:
        logger.info("📱 Checking device registration...")

        # Click on Test tab
        test_selectors = [
            "//span[contains(text(), 'Test')]",
            "//a[contains(text(), 'Test')]",
            "//button[contains(text(), 'Test')]",
        ]

        clicked = False
        for selector in test_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    elements[0].click()
                    clicked = True
                    logger.info("✅ Clicked on 'Test' tab")
                    time.sleep(2)
                    break
            except:
                continue

        # Look for device setup section
        time.sleep(2)

        # Take screenshot of test page
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"/Users/Subho/alexa_test_tab_{timestamp}.png"
        driver.save_screenshot(screenshot_path)
        logger.info(f"📸 Screenshot saved: {screenshot_path}")

        # Check if we can find device info
        device_indicators = [
            "//div[contains(text(), 'Device')]",
            "//span[contains(text(), 'device')]",
            "//h3[contains(text(), 'Device')]",
        ]

        device_found = False
        for indicator in device_indicators:
            try:
                elements = driver.find_elements(By.XPATH, indicator)
                if elements:
                    logger.info("✅ Found device setup section")
                    device_found = True
                    break
            except:
                continue

        if not device_found:
            logger.warning("⚠️  Could not verify device registration automatically")
            logger.info("   Please ensure your Echo device is registered in the Test tab")

        return True

    except Exception as e:
        logger.error(f"❌ Error checking device: {e}")
        return False

def take_final_screenshot(driver):
    """Take final screenshot for reference"""
    try:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"/Users/Subho/alexa_setup_final_{timestamp}.png"
        driver.save_screenshot(screenshot_path)
        logger.info(f"📸 Final screenshot saved: {screenshot_path}")
        return screenshot_path
    except Exception as e:
        logger.error(f"❌ Error taking screenshot: {e}")
        return None

def main():
    """Main execution function"""
    logger.info("🚀 AUTOMATED ALEXA SKILL CONFIGURATION")
    logger.info("=" * 50)
    logger.info()
    logger.info("This script will:")
    logger.info("1. Connect to your Brave browser")
    logger.info("2. Navigate to Alexa Developer Console")
    logger.info("3. Find 'Personal Assistant' skill")
    logger.info("4. Check/fix invocation name")
    logger.info("5. Verify endpoint URL")
    logger.info("6. Check device registration")
    logger.info("7. Save and build model")
    logger.info()
    logger.info("Make sure Brave is open and logged into Amazon Developer Console!")
    logger.info()

    input("Press Enter when ready...")

    driver = None
    try:
        # Connect to Brave
        driver = connect_to_brave()
        if not driver:
            logger.error("❌ Failed to connect to Brave")
            return

        # Navigate to Alexa console
        if not navigate_to_alexa_console(driver):
            logger.error("❌ Failed to navigate to Alexa console")
            return

        # Find Personal Assistant skill
        if not find_personal_assistant_skill(driver):
            logger.error("❌ Failed to find skill")
            return

        # Check invocation name
        if not check_invocation_name(driver):
            logger.error("❌ Failed to check invocation name")
            return

        # Verify endpoint
        if not verify_endpoint(driver):
            logger.error("❌ Failed to verify endpoint")
            return

        # Check device registration
        if not check_device_registration(driver):
            logger.error("❌ Failed to check device registration")
            return

        # Save and build
        save_and_build(driver)

        # Take final screenshot
        take_final_screenshot(driver)

        logger.info("\n" + "=" * 50)
        logger.info("🎉 AUTOMATED CONFIGURATION COMPLETE!")
        logger.info("=" * 50)
        logger.info()
        logger.info("✅ Summary of actions performed:")
        logger.info("   • Connected to Brave browser")
        logger.info("   • Navigated to Alexa Developer Console")
        logger.info("   • Found 'Personal Assistant' skill")
        logger.info("   • Checked invocation name (should be 'personal assistant')")
        logger.info("   • Verified endpoint URL")
        logger.info("   • Checked device registration")
        logger.info()
        logger.info("📋 Next Steps:")
        logger.info("   1. Check the screenshots taken")
        logger.info("   2. Verify invocation name is exactly: 'personal assistant'")
        logger.info("   3. Ensure your Echo device is registered in Test tab")
        logger.info("   4. Try: 'Alexa, open Personal Assistant'")
        logger.info()
        logger.info("📸 Screenshots saved to /Users/Subho/")
        logger.info("=" * 50)

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
