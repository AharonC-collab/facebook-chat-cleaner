from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time
import logging
import argparse
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"fb_cleaner_final_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

def setup_driver():
    """Setup and return Chrome webdriver"""
    options = Options()
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

def click_element_safely(driver, element):
    """Try multiple methods to click an element safely"""
    try:
        # Try regular left click first
        logger.info("Attempting regular left click")
        element.click()
        return True
    except Exception as e:
        logger.warning(f"Regular click failed: {str(e)}")
        try:
            # Try JavaScript click
            logger.info("Attempting JavaScript click")
            driver.execute_script("arguments[0].click();", element)
            return True
        except Exception as e:
            logger.warning(f"JavaScript click failed: {str(e)}")
            try:
                # Try ActionChains click
                logger.info("Attempting ActionChains click")
                ActionChains(driver).move_to_element(element).click().perform()
                return True
            except Exception as e:
                logger.error(f"All click methods failed: {str(e)}")
                return False

def delete_chats(driver, max_chats=None):
    """Delete Facebook Messenger chats by opening each chat first"""
    deleted_count = 0
    error_count = 0
    
    # Navigate to the Messages page
    driver.get("https://www.facebook.com/messages/")
    logger.info("Opened Facebook Messages page")
    
    # Let user log in manually
    input("ud83dudfe2 Log in to Facebook manually, then press ENTER to continue...")
    logger.info("User logged in, proceeding with deletion")
    
    # Give time for the page to load completely
    time.sleep(5)
    
    while True:
        try:
            # Find all chat items in the left sidebar
            chat_items = driver.find_elements(By.XPATH, 
                '//div[@role="row"] | //div[@role="listitem"] | //div[contains(@aria-label, "Conversation")]')
            
            if not chat_items or len(chat_items) == 0:
                logger.info("No more chat items found.")
                break
                
            logger.info(f"Found {len(chat_items)} chat items")
            
            # Get the first chat item
            current_chat = chat_items[0]
            
            # Step 1: Click on the chat to open it
            logger.info("Step 1: Left-clicking on chat to open it")
            if not click_element_safely(driver, current_chat):
                logger.error("Failed to click on chat, skipping")
                error_count += 1
                continue
            
            # Wait for the chat to load
            time.sleep(3)
            
            # Step 2: Look for the three dots menu button in the chat window
            logger.info("Step 2: Looking for menu button in chat window")
            
            # Try multiple selectors for the menu button
            menu_buttons = driver.find_elements(By.XPATH, 
                '//div[contains(@aria-label, "More") or contains(@aria-label, "Menu") or ' +
                'contains(@aria-label, "u05e2u05d5u05d3") or contains(@aria-label, "u05eau05e4u05e8u05d9u05d8")]')
            
            if not menu_buttons or len(menu_buttons) == 0:
                # Try alternative selectors
                menu_buttons = driver.find_elements(By.XPATH, 
                    '//div[@role="button"] | //span[contains(text(), "...")]')
            
            if not menu_buttons or len(menu_buttons) == 0:
                logger.warning("No menu button found, trying to find by position")
                # Try to find buttons in the top area of the chat
                top_buttons = driver.find_elements(By.XPATH, 
                    '//div[contains(@style, "top") and @role="button"]')
                
                if top_buttons and len(top_buttons) > 0:
                    menu_buttons = [top_buttons[-1]]  # Use the last button in the top area
            
            if menu_buttons and len(menu_buttons) > 0:
                logger.info(f"Found {len(menu_buttons)} potential menu buttons, clicking the last one")
                if not click_element_safely(driver, menu_buttons[-1]):
                    logger.error("Failed to click menu button, trying alternative approach")
                    # Try alternative approach
                    if not try_alternative_delete(driver):
                        error_count += 1
                        continue
                
                # Wait for menu to appear
                time.sleep(2)
                
                # Step 3: Look for delete option in the menu
                logger.info("Step 3: Looking for delete option")
                delete_options = driver.find_elements(By.XPATH, 
                    '//div[contains(text(), "Delete") or contains(text(), "Remove") or ' +
                    'contains(text(), "u05deu05d7u05e7") or contains(text(), "u05d4u05e1u05e8")]')
                
                if delete_options and len(delete_options) > 0:
                    logger.info(f"Found {len(delete_options)} delete options, clicking the first one")
                    if not click_element_safely(driver, delete_options[0]):
                        logger.error("Failed to click delete option, trying alternative approach")
                        # Try alternative approach
                        if not try_alternative_delete(driver):
                            error_count += 1
                            continue
                    
                    # Wait for confirmation dialog
                    time.sleep(2)
                    
                    # Step 4: Confirm deletion
                    logger.info("Step 4: Looking for confirmation button")
                    confirm_buttons = driver.find_elements(By.XPATH, 
                        '//div[@role="button"]//div[contains(text(), "Delete") or ' +
                        'contains(text(), "u05deu05d7u05e7") or contains(text(), "u05d4u05e1u05e8") or ' +
                        'contains(text(), "Confirm") or contains(text(), "u05d0u05d9u05e9u05d5u05e8")]')
                    
                    if confirm_buttons and len(confirm_buttons) > 0:
                        logger.info("Found confirmation button, clicking it")
                        if click_element_safely(driver, confirm_buttons[0]):
                            # Wait for deletion to complete
                            time.sleep(3)
                            deleted_count += 1
                            logger.info(f"u2705 Successfully deleted chat {deleted_count}")
                            error_count = 0  # Reset error count on success
                        else:
                            logger.error("Failed to click confirmation button")
                            error_count += 1
                    else:
                        logger.warning("No confirmation button found, trying alternative approach")
                        # Try alternative approach
                        if try_alternative_delete(driver):
                            deleted_count += 1
                            logger.info(f"u2705 Successfully deleted chat {deleted_count} using alternative method")
                            error_count = 0  # Reset error count on success
                        else:
                            error_count += 1
                else:
                    logger.warning("No delete option found, trying alternative approach")
                    # Try alternative approach
                    if try_alternative_delete(driver):
                        deleted_count += 1
                        logger.info(f"u2705 Successfully deleted chat {deleted_count} using alternative method")
                        error_count = 0  # Reset error count on success
                    else:
                        error_count += 1
            else:
                logger.warning("No menu button found, trying alternative approach")
                # Try alternative approach
                if try_alternative_delete(driver):
                    deleted_count += 1
                    logger.info(f"u2705 Successfully deleted chat {deleted_count} using alternative method")
                    error_count = 0  # Reset error count on success
                else:
                    error_count += 1
            
            # Check if we've reached the maximum number of chats to delete
            if max_chats and deleted_count >= max_chats:
                logger.info(f"Reached maximum number of chats to delete ({max_chats})")
                break
                
            # If we've had too many errors in a row, refresh the page
            if error_count >= 3:
                logger.info("Too many errors, refreshing page")
                driver.refresh()
                time.sleep(5)
                error_count = 0
                
            # Go back to the chat list or refresh the page to see updated list
            logger.info("Returning to chat list")
            try:
                # Try to find and click a back button
                back_buttons = driver.find_elements(By.XPATH, 
                    '//div[contains(@aria-label, "Back") or contains(@aria-label, "u05d7u05d6u05d5u05e8")]')
                
                if back_buttons and len(back_buttons) > 0:
                    logger.info("Found back button, clicking it")
                    click_element_safely(driver, back_buttons[0])
                else:
                    # If no back button, just refresh the page
                    logger.info("No back button found, refreshing page")
                    driver.refresh()
            except Exception as e:
                logger.warning(f"Error returning to chat list: {str(e)}, refreshing page")
                driver.refresh()
            
            # Wait for page to load
            time.sleep(5)
            
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            error_count += 1
            if error_count >= 3:
                logger.info("Too many errors, refreshing page")
                driver.refresh()
                time.sleep(5)
                error_count = 0
    
    return deleted_count

def try_alternative_delete(driver):
    """Try alternative methods to delete a chat"""
    try:
        # Method 1: Try to find any visible delete buttons
        logger.info("Alternative method 1: Looking for any visible delete buttons")
        delete_buttons = driver.find_elements(By.XPATH, 
            '//div[contains(text(), "Delete") or contains(text(), "Remove") or ' +
            'contains(text(), "u05deu05d7u05e7") or contains(text(), "u05d4u05e1u05e8")]')
        
        if delete_buttons and len(delete_buttons) > 0:
            logger.info("Found delete button, clicking it")
            if click_element_safely(driver, delete_buttons[0]):
                time.sleep(2)
                
                # Look for confirm button
                confirm_buttons = driver.find_elements(By.XPATH, 
                    '//div[@role="button"]//div[contains(text(), "Delete") or ' +
                    'contains(text(), "u05deu05d7u05e7") or contains(text(), "u05d4u05e1u05e8") or ' +
                    'contains(text(), "Confirm") or contains(text(), "u05d0u05d9u05e9u05d5u05e8")]')
                
                if confirm_buttons and len(confirm_buttons) > 0:
                    logger.info("Found confirmation button, clicking it")
                    if click_element_safely(driver, confirm_buttons[0]):
                        time.sleep(3)
                        return True
        
        # Method 2: Try using keyboard shortcuts
        logger.info("Alternative method 2: Using keyboard shortcuts")
        
        # Try Delete key
        ActionChains(driver).send_keys(Keys.DELETE).perform()
        time.sleep(2)
        
        # Look for confirm button
        confirm_buttons = driver.find_elements(By.XPATH, 
            '//div[@role="button"]//div[contains(text(), "Delete") or ' +
            'contains(text(), "u05deu05d7u05e7") or contains(text(), "u05d4u05e1u05e8") or ' +
            'contains(text(), "Confirm") or contains(text(), "u05d0u05d9u05e9u05d5u05e8")]')
        
        if confirm_buttons and len(confirm_buttons) > 0:
            logger.info("Found confirmation button after keyboard shortcut, clicking it")
            if click_element_safely(driver, confirm_buttons[0]):
                time.sleep(3)
                return True
        
        # Method 3: Try to use the gear icon or settings
        logger.info("Alternative method 3: Looking for gear icon or settings")
        gear_buttons = driver.find_elements(By.XPATH, 
            '//div[contains(@aria-label, "Settings") or contains(@aria-label, "u05d4u05d2u05d3u05e8u05d5u05ea")]')
        
        if gear_buttons and len(gear_buttons) > 0:
            logger.info("Found settings button, clicking it")
            if click_element_safely(driver, gear_buttons[0]):
                time.sleep(2)
                
                # Look for delete option
                delete_options = driver.find_elements(By.XPATH, 
                    '//div[contains(text(), "Delete") or contains(text(), "Remove") or ' +
                    'contains(text(), "u05deu05d7u05e7") or contains(text(), "u05d4u05e1u05e8")]')
                
                if delete_options and len(delete_options) > 0:
                    logger.info("Found delete option in settings, clicking it")
                    if click_element_safely(driver, delete_options[0]):
                        time.sleep(2)
                        
                        # Look for confirm button
                        confirm_buttons = driver.find_elements(By.XPATH, 
                            '//div[@role="button"]//div[contains(text(), "Delete") or ' +
                            'contains(text(), "u05deu05d7u05e7") or contains(text(), "u05d4u05e1u05e8") or ' +
                            'contains(text(), "Confirm") or contains(text(), "u05d0u05d9u05e9u05d5u05e8")]')
                        
                        if confirm_buttons and len(confirm_buttons) > 0:
                            logger.info("Found confirmation button, clicking it")
                            if click_element_safely(driver, confirm_buttons[0]):
                                time.sleep(3)
                                return True
        
        # Method 4: Try direct JavaScript approach
        logger.info("Alternative method 4: Using direct JavaScript")
        
        # Try to find and click delete buttons directly using JavaScript
        result = driver.execute_script("""
            // Try to find delete buttons or links
            var deleteElements = [];
            var elements = document.querySelectorAll('div, span, a');
            for (var i = 0; i < elements.length; i++) {
                var el = elements[i];
                var text = el.textContent.toLowerCase();
                if (text.includes('delete') || text.includes('remove') || 
                    text.includes('u05deu05d7u05e7') || text.includes('u05d4u05e1u05e8')) {
                    deleteElements.push(el);
                }
            }
            // Click the first delete element found
            if (deleteElements.length > 0) {
                deleteElements[0].click();
                return true;
            }
            return false;
        """)
        
        if result:
            logger.info("JavaScript found and clicked a delete element")
            time.sleep(2)
            
            # Look for confirm button
            confirm_buttons = driver.find_elements(By.XPATH, 
                '//div[@role="button"]//div[contains(text(), "Delete") or ' +
                'contains(text(), "u05deu05d7u05e7") or contains(text(), "u05d4u05e1u05e8") or ' +
                'contains(text(), "Confirm") or contains(text(), "u05d0u05d9u05e9u05d5u05e8")]')
            
            if confirm_buttons and len(confirm_buttons) > 0:
                logger.info("Found confirmation button after JavaScript, clicking it")
                if click_element_safely(driver, confirm_buttons[0]):
                    time.sleep(3)
                    return True
        
        return False
    except Exception as e:
        logger.error(f"Error in alternative delete methods: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Facebook Messenger Chat Cleaner - Final Version')
    parser.add_argument('--max', type=int, help='Maximum number of chats to delete')
    args = parser.parse_args()
    
    logger.info("Starting Facebook Messenger Chat Cleaner - Final Version")
    
    # Setup Chrome
    driver = setup_driver()
    
    try:
        # Delete chats
        deleted = delete_chats(driver, max_chats=args.max)
        
        logger.info(f"ud83cudf89 Done! Successfully deleted {deleted} chats.")
        logger.info("You can re-run the script to delete more chats if needed.")
        
    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
    finally:
        # Clean up
        driver.quit()
        logger.info("Browser closed")

if __name__ == "__main__":
    main()
