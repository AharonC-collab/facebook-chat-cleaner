from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException
import time
import logging
import argparse
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"fb_message_cleaner_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

def setup_driver(headless=False):
    """Setup and return a configured Chrome webdriver"""
    options = Options()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    
    # Create driver
    driver = webdriver.Chrome(options=options)
    return driver

def wait_for_element(driver, by, selector, timeout=10):
    """Wait for an element to be present and return it"""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, selector))
        )
        return element
    except TimeoutException:
        logger.warning(f"Timeout waiting for element: {selector}")
        return None

def delete_chats(driver, max_chats=None, wait_time=3):
    """Delete Facebook Messenger chats"""
    # Give time for Messenger to finish loading
    time.sleep(5)
    
    deleted_count = 0
    error_count = 0
    
    # Hebrew and English text variations for Delete Chat
    delete_chat_texts = ["Delete Chat", "מחק צ'אט", "מחק שיחה", "הסר"]
    
    # Confirmation button texts in Hebrew and English
    confirm_texts = ["Delete", "מחק", "הסר", "אישור"]
    
    while True:
        try:
            # Find all chat rows first
            chat_rows = driver.find_elements(By.XPATH, '//div[@role="row"]')
            
            if not chat_rows:
                logger.info("No more chat rows found.")
                break
                
            logger.info(f"Found {len(chat_rows)} chat rows")
            
            # Process the first chat row
            try:
                # Based on the screenshot, we need to hover specifically on the right side of the chat row
                # to make the three-dot menu appear
                logger.info("Hovering over right side of first chat to reveal menu button")
                
                # Get the dimensions of the chat row
                row_width = chat_rows[0].size['width']
                row_height = chat_rows[0].size['height']
                
                # Create an action chain to move to the right side of the chat row
                actions = webdriver.ActionChains(driver)
                
                # Move to the chat row first (to ensure it's in view)
                actions.move_to_element(chat_rows[0]).perform()
                time.sleep(0.5)
                
                # Then move to the right side of the chat row (about 90% of the way across)
                # This is where the three-dot menu typically appears
                actions = webdriver.ActionChains(driver)
                actions.move_to_element_with_offset(chat_rows[0], int(row_width * 0.9), int(row_height / 2)).perform()
                time.sleep(1)  # Wait for menu to appear
                
                # Look for any visible buttons that might be the three-dot menu
                # First try to find by aria-label
                menu_buttons = driver.find_elements(By.XPATH, 
                    '//div[@role="row"][1]//div[contains(@aria-label, "More") or contains(@aria-label, "עוד") or contains(@aria-label, "אפשרויות")]')
                
                if not menu_buttons:
                    # Try to find any visible buttons on the right side of the row
                    logger.info("No labeled menu buttons found, looking for any buttons on the right side")
                    menu_buttons = driver.find_elements(By.XPATH, '//div[@role="row"][1]//div[@role="button"]')
                
                if not menu_buttons:
                    # Try clicking directly where the menu button should be
                    logger.warning("No menu buttons found, trying to click directly where it should be")
                    actions = webdriver.ActionChains(driver)
                    actions.move_to_element_with_offset(chat_rows[0], int(row_width * 0.95), int(row_height / 2)).click().perform()
                    time.sleep(1)
                else:
                    # Click the last button (most likely to be the menu)
                    logger.info(f"Found {len(menu_buttons)} potential menu buttons, clicking the last one")
                    menu_buttons[-1].click()
                    time.sleep(1)
            except (StaleElementReferenceException, ElementClickInterceptedException):
                logger.warning("Menu button is stale or intercepted, refreshing page")
                driver.refresh()
                time.sleep(5)
                continue
            except Exception as e:
                logger.error(f"Error clicking menu button: {str(e)}")
                error_count += 1
                if error_count > 5:
                    logger.info("Too many errors, refreshing page")
                    driver.refresh()
                    time.sleep(5)
                    error_count = 0
                continue
            
            # Look for the Delete Chat option in the menu
            delete_success = False
            
            # Try to find and click the Delete Chat option (with multiple language variations)
            for text in delete_chat_texts:
                try:
                    # Try to find Delete Chat by text content
                    delete_elements = driver.find_elements(By.XPATH, 
                        f'//span[contains(text(), "{text}")]/../.. | //div[contains(text(), "{text}")]')
                    
                    if delete_elements:
                        logger.info(f"Found Delete Chat option with text: {text}")
                        delete_elements[0].click()
                        delete_success = True
                        break
                except Exception as e:
                    logger.warning(f"Error finding delete option with text '{text}': {str(e)}")
            
            # If we couldn't find the Delete Chat option by text, try by position (last item in menu)
            if not delete_success:
                try:
                    # Based on the screenshot, Delete Chat is the last option in the menu
                    # Try to get all menu items and click the last one
                    menu_items = driver.find_elements(By.XPATH, '//div[@role="menu"]/div/div')
                    if menu_items and len(menu_items) >= 7:  # Delete Chat is usually the 7th item
                        logger.info("Trying to click the last menu item (likely Delete Chat)")
                        menu_items[-1].click()  # Click the last item
                        delete_success = True
                except Exception as e:
                    logger.error(f"Error clicking last menu item: {str(e)}")
            
            if not delete_success:
                logger.warning("Could not find Delete Chat option, skipping this chat")
                # Close the menu by clicking elsewhere
                try:
                    driver.find_element(By.XPATH, '//body').click()
                except:
                    pass
                error_count += 1
                continue
            
            # Wait for confirmation dialog
            time.sleep(1)
            
            # Try to confirm deletion
            confirm_success = False
            
            # Try different approaches to find and click the confirmation button
            for text in confirm_texts:
                try:
                    # Try to find confirmation button by text
                    confirm_buttons = driver.find_elements(By.XPATH, 
                        f'//div[@role="button"]/div/div/span[contains(text(), "{text}")]/..')
                    
                    if confirm_buttons:
                        logger.info(f"Found confirmation button with text: {text}")
                        confirm_buttons[0].click()
                        confirm_success = True
                        break
                except Exception as e:
                    logger.warning(f"Error finding confirmation button with text '{text}': {str(e)}")
            
            # If we couldn't find the confirmation button by text, try by dialog button position
            if not confirm_success:
                try:
                    # Try to get all buttons in the confirmation dialog and click the right one
                    dialog_buttons = driver.find_elements(By.XPATH, '//div[@role="dialog"]//div[@role="button"]')
                    if dialog_buttons and len(dialog_buttons) >= 2:
                        logger.info("Trying to click the confirmation button by position")
                        dialog_buttons[-1].click()  # Usually the rightmost/last button confirms
                        confirm_success = True
                except Exception as e:
                    logger.error(f"Error clicking confirmation button by position: {str(e)}")
            
            if not confirm_success:
                logger.warning("Could not find confirmation button, skipping this chat")
                # Try to close any open dialogs by pressing Escape
                try:
                    from selenium.webdriver.common.keys import Keys
                    webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                except:
                    pass
                error_count += 1
                continue
            
            # Wait for deletion to complete
            time.sleep(wait_time)
            
            deleted_count += 1
            logger.info(f"✅ Successfully deleted chat {deleted_count}")
            
            # Check if we've reached the maximum number of chats to delete
            if max_chats and deleted_count >= max_chats:
                logger.info(f"Reached maximum number of chats to delete ({max_chats})")
                break
                
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            error_count += 1
            # Refresh the page if we encounter too many errors
            if error_count > 5:
                logger.info("Too many errors, refreshing page...")
                driver.refresh()
                time.sleep(5)
                error_count = 0
    
    return deleted_count

def main():
    parser = argparse.ArgumentParser(description='Facebook Messenger Chat Cleaner')
    parser.add_argument('--max', type=int, help='Maximum number of chats to delete')
    parser.add_argument('--wait', type=int, default=3, help='Wait time between actions (seconds)')
    args = parser.parse_args()
    
    logger.info("Starting Facebook Messenger Chat Cleaner")
    
    # Setup Chrome
    driver = setup_driver(headless=False)  # Headless mode won't work for login
    
    try:
        # Navigate to Facebook Messages
        driver.get("https://www.facebook.com/messages")
        logger.info("Opened Facebook Messages page")
        
        # Let user log in manually
        input("🟢 Log in to Facebook manually, then press ENTER to continue...")
        logger.info("User logged in, proceeding with deletion")
        
        # Delete chats
        deleted = delete_chats(driver, max_chats=args.max, wait_time=args.wait)
        
        logger.info(f"🎉 Done! Successfully deleted {deleted} chats.")
        logger.info("You can scroll down and re-run the script to delete more chats if needed.")
        
    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
    finally:
        # Clean up
        driver.quit()
        logger.info("Browser closed")

if __name__ == "__main__":
    main()
