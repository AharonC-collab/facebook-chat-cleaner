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
        logging.FileHandler(f"fb_cleaner_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
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
        # Try regular click first
        element.click()
        return True
    except Exception as e:
        logger.warning(f"Regular click failed: {str(e)}")
        try:
            # Try JavaScript click
            driver.execute_script("arguments[0].click();", element)
            return True
        except Exception as e:
            logger.warning(f"JavaScript click failed: {str(e)}")
            try:
                # Try ActionChains click
                ActionChains(driver).move_to_element(element).click().perform()
                return True
            except Exception as e:
                logger.error(f"All click methods failed: {str(e)}")
                return False

def delete_chats(driver, max_chats=None):
    """Delete Facebook Messenger chats using direct targeting of chat elements"""
    deleted_count = 0
    error_count = 0
    
    # Navigate to the Messages page
    driver.get("https://www.facebook.com/messages/")
    logger.info("Opened Facebook Messages page")
    
    # Let user log in manually
    input("🟢 Log in to Facebook manually, then press ENTER to continue...")
    logger.info("User logged in, proceeding with deletion")
    
    # Give time for the page to load completely
    time.sleep(5)
    
    while True:
        try:
            # Based on the screenshot, we need to target the chat list items
            # These appear to be in the left sidebar
            chat_items = driver.find_elements(By.XPATH, '//div[contains(@role, "row") or contains(@role, "listitem")]')
            
            if not chat_items or len(chat_items) == 0:
                logger.info("No more chat items found.")
                break
                
            logger.info(f"Found {len(chat_items)} chat items")
            
            # Process the first chat item
            current_chat = chat_items[0]
            
            # First, try to right-click on the chat to open context menu
            logger.info("Right-clicking on chat to open context menu")
            ActionChains(driver).context_click(current_chat).perform()
            time.sleep(2)
            
            # Look for delete option in context menu
            delete_options = driver.find_elements(By.XPATH, 
                '//div[contains(text(), "Delete") or contains(text(), "מחק") or contains(text(), "הסר")]')
            
            if delete_options and len(delete_options) > 0:
                logger.info("Found delete option in context menu, clicking it")
                click_element_safely(driver, delete_options[0])
                time.sleep(2)
                
                # Look for confirm button
                confirm_buttons = driver.find_elements(By.XPATH, 
                    '//div[@role="button"]//div[contains(text(), "Delete") or contains(text(), "מחק") or contains(text(), "הסר")]')
                
                if confirm_buttons and len(confirm_buttons) > 0:
                    logger.info("Found confirmation button, clicking it")
                    click_element_safely(driver, confirm_buttons[0])
                    time.sleep(3)
                    deleted_count += 1
                    logger.info(f"✅ Successfully deleted chat {deleted_count}")
                else:
                    logger.warning("No confirmation button found, trying alternative method")
                    # Try alternative method
                    if try_alternative_delete(driver, current_chat):
                        deleted_count += 1
                        logger.info(f"✅ Successfully deleted chat {deleted_count} using alternative method")
                    else:
                        error_count += 1
            else:
                logger.warning("No delete option found in context menu, trying alternative method")
                # Try alternative method
                if try_alternative_delete(driver, current_chat):
                    deleted_count += 1
                    logger.info(f"✅ Successfully deleted chat {deleted_count} using alternative method")
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
                
            # Give the page time to update
            time.sleep(3)
            
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            error_count += 1
            if error_count >= 3:
                logger.info("Too many errors, refreshing page")
                driver.refresh()
                time.sleep(5)
                error_count = 0
    
    return deleted_count

def try_alternative_delete(driver, chat_element):
    """Try alternative methods to delete a chat"""
    try:
        # Method 1: Try clicking on the chat first to select it
        logger.info("Alternative method 1: Clicking chat to select it")
        click_element_safely(driver, chat_element)
        time.sleep(2)
        
        # Look for any menu button or three dots after selecting the chat
        menu_buttons = driver.find_elements(By.XPATH, 
            '//div[contains(@aria-label, "More") or contains(@aria-label, "עוד") or contains(@aria-label, "אפשרויות")]')
        
        if menu_buttons and len(menu_buttons) > 0:
            logger.info("Found menu button, clicking it")
            click_element_safely(driver, menu_buttons[0])
            time.sleep(2)
            
            # Look for delete option in the menu
            delete_options = driver.find_elements(By.XPATH, 
                '//div[contains(text(), "Delete") or contains(text(), "מחק") or contains(text(), "הסר")]')
            
            if delete_options and len(delete_options) > 0:
                logger.info("Found delete option in menu, clicking it")
                click_element_safely(driver, delete_options[0])
                time.sleep(2)
                
                # Look for confirm button
                confirm_buttons = driver.find_elements(By.XPATH, 
                    '//div[@role="button"]//div[contains(text(), "Delete") or contains(text(), "מחק") or contains(text(), "הסר")]')
                
                if confirm_buttons and len(confirm_buttons) > 0:
                    logger.info("Found confirmation button, clicking it")
                    click_element_safely(driver, confirm_buttons[0])
                    time.sleep(3)
                    return True
        
        # Method 2: Try using the main Facebook menu
        logger.info("Alternative method 2: Using main Facebook menu")
        
        # Based on your screenshot, there's a main menu button at the top
        # Try to find and click it
        main_menu_buttons = driver.find_elements(By.XPATH, 
            '//div[@aria-label="Menu" or @aria-label="תפריט"]')
        
        if main_menu_buttons and len(main_menu_buttons) > 0:
            logger.info("Found main menu button, clicking it")
            click_element_safely(driver, main_menu_buttons[0])
            time.sleep(2)
            
            # Look for messages or messaging option
            message_options = driver.find_elements(By.XPATH, 
                '//span[contains(text(), "Messages") or contains(text(), "הודעות")]')
            
            if message_options and len(message_options) > 0:
                logger.info("Found messages option, clicking it")
                click_element_safely(driver, message_options[0])
                time.sleep(2)
                
                # Now try to find and click on the first chat again
                chat_items = driver.find_elements(By.XPATH, '//div[contains(@role, "row") or contains(@role, "listitem")]')
                if chat_items and len(chat_items) > 0:
                    logger.info("Found chat item again, clicking it")
                    click_element_safely(driver, chat_items[0])
                    time.sleep(2)
                    
                    # Try to find delete or remove option
                    delete_options = driver.find_elements(By.XPATH, 
                        '//div[contains(text(), "Delete") or contains(text(), "מחק") or contains(text(), "הסר")]')
                    
                    if delete_options and len(delete_options) > 0:
                        logger.info("Found delete option, clicking it")
                        click_element_safely(driver, delete_options[0])
                        time.sleep(2)
                        
                        # Look for confirm button
                        confirm_buttons = driver.find_elements(By.XPATH, 
                            '//div[@role="button"]//div[contains(text(), "Delete") or contains(text(), "מחק") or contains(text(), "הסר")]')
                        
                        if confirm_buttons and len(confirm_buttons) > 0:
                            logger.info("Found confirmation button, clicking it")
                            click_element_safely(driver, confirm_buttons[0])
                            time.sleep(3)
                            return True
        
        # Method 3: Try using keyboard shortcuts
        logger.info("Alternative method 3: Using keyboard shortcuts")
        
        # First select the chat again to ensure it's focused
        click_element_safely(driver, chat_element)
        time.sleep(1)
        
        # Try Delete key
        ActionChains(driver).send_keys(Keys.DELETE).perform()
        time.sleep(2)
        
        # Look for confirm button
        confirm_buttons = driver.find_elements(By.XPATH, 
            '//div[@role="button"]//div[contains(text(), "Delete") or contains(text(), "מחק") or contains(text(), "הסר")]')
        
        if confirm_buttons and len(confirm_buttons) > 0:
            logger.info("Found confirmation button after keyboard shortcut, clicking it")
            click_element_safely(driver, confirm_buttons[0])
            time.sleep(3)
            return True
        
        # Method 4: Try hovering over the chat to reveal options
        logger.info("Alternative method 4: Hovering over chat to reveal options")
        
        # Hover over the chat
        ActionChains(driver).move_to_element(chat_element).perform()
        time.sleep(2)
        
        # Look for any buttons that appear on hover
        hover_buttons = driver.find_elements(By.XPATH, 
            '//div[@role="button" and not(contains(@style, "display: none"))]')
        
        if hover_buttons and len(hover_buttons) > 0:
            logger.info(f"Found {len(hover_buttons)} buttons after hovering, clicking the last one")
            # Usually the last button is for more options or delete
            click_element_safely(driver, hover_buttons[-1])
            time.sleep(2)
            
            # Look for delete option
            delete_options = driver.find_elements(By.XPATH, 
                '//div[contains(text(), "Delete") or contains(text(), "מחק") or contains(text(), "הסר")]')
            
            if delete_options and len(delete_options) > 0:
                logger.info("Found delete option after hovering, clicking it")
                click_element_safely(driver, delete_options[0])
                time.sleep(2)
                
                # Look for confirm button
                confirm_buttons = driver.find_elements(By.XPATH, 
                    '//div[@role="button"]//div[contains(text(), "Delete") or contains(text(), "מחק") or contains(text(), "הסר")]')
                
                if confirm_buttons and len(confirm_buttons) > 0:
                    logger.info("Found confirmation button, clicking it")
                    click_element_safely(driver, confirm_buttons[0])
                    time.sleep(3)
                    return True
        
        # Method 5: Try direct JavaScript approach
        logger.info("Alternative method 5: Using direct JavaScript")
        
        # Try to find and click delete buttons directly using JavaScript
        result = driver.execute_script("""
            // Try to find delete buttons or links
            var deleteElements = [];
            var elements = document.querySelectorAll('div, span, a');
            for (var i = 0; i < elements.length; i++) {
                var el = elements[i];
                var text = el.textContent.toLowerCase();
                if (text.includes('delete') || text.includes('מחק') || text.includes('הסר')) {
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
                '//div[@role="button"]//div[contains(text(), "Delete") or contains(text(), "מחק") or contains(text(), "הסר")]')
            
            if confirm_buttons and len(confirm_buttons) > 0:
                logger.info("Found confirmation button after JavaScript, clicking it")
                click_element_safely(driver, confirm_buttons[0])
                time.sleep(3)
                return True
        
        return False
    except Exception as e:
        logger.error(f"Error in alternative delete methods: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Facebook Messenger Chat Cleaner V2')
    parser.add_argument('--max', type=int, help='Maximum number of chats to delete')
    args = parser.parse_args()
    
    logger.info("Starting Facebook Messenger Chat Cleaner V2")
    
    # Setup Chrome
    driver = setup_driver()
    
    try:
        # Delete chats
        deleted = delete_chats(driver, max_chats=args.max)
        
        logger.info(f"🎉 Done! Successfully deleted {deleted} chats.")
        logger.info("You can re-run the script to delete more chats if needed.")
        
    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
    finally:
        # Clean up
        driver.quit()
        logger.info("Browser closed")

if __name__ == "__main__":
    main()
