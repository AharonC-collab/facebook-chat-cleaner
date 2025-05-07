from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import logging
import argparse
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"fb_delete_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
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

def delete_chats(driver, max_chats=None):
    """Delete Facebook Messenger chats using direct JavaScript execution"""
    deleted_count = 0
    
    # Navigate to the Messages page
    driver.get("https://www.facebook.com/messages")
    logger.info("Opened Facebook Messages page")
    
    # Let user log in manually
    input("🟢 Log in to Facebook manually, then press ENTER to continue...")
    logger.info("User logged in, proceeding with deletion")
    
    # Give time for the page to load completely
    time.sleep(5)
    
    while True:
        try:
            # Find all chat rows
            chat_rows = driver.find_elements(By.XPATH, '//div[@role="row"]')
            
            if not chat_rows or len(chat_rows) == 0:
                logger.info("No more chat rows found.")
                break
                
            logger.info(f"Found {len(chat_rows)} chat rows")
            
            # Process the first chat row
            current_chat = chat_rows[0]
            
            # Use JavaScript to simulate a right-click on the chat row
            # This often brings up a context menu with delete options
            logger.info("Simulating right-click on chat row")
            driver.execute_script("""
                var element = arguments[0];
                var event = new MouseEvent('contextmenu', {
                    'view': window,
                    'bubbles': true,
                    'cancelable': true
                });
                element.dispatchEvent(event);
            """, current_chat)
            
            time.sleep(2)
            
            # Look for delete option in the context menu
            delete_options = driver.find_elements(By.XPATH, 
                '//div[contains(text(), "Delete") or contains(text(), "מחק") or contains(text(), "הסר")]')
            
            if delete_options:
                logger.info(f"Found {len(delete_options)} delete options")
                # Click the first delete option
                delete_options[0].click()
                time.sleep(2)
                
                # Look for confirm button in any dialog that appears
                confirm_buttons = driver.find_elements(By.XPATH, 
                    '//div[@role="button"]//div[contains(text(), "Delete") or contains(text(), "מחק") or contains(text(), "הסר") or contains(text(), "אישור")]')
                
                if confirm_buttons:
                    logger.info("Found confirmation button, clicking it")
                    confirm_buttons[0].click()
                    time.sleep(3)
                    deleted_count += 1
                    logger.info(f"✅ Successfully deleted chat {deleted_count}")
                else:
                    logger.warning("No confirmation button found, trying alternative approach")
                    # Try an alternative approach - click directly on the chat
                    try_alternative_delete(driver, current_chat)
            else:
                logger.warning("No delete options found in context menu, trying alternative approach")
                # Try an alternative approach
                success = try_alternative_delete(driver, current_chat)
                if success:
                    deleted_count += 1
                    logger.info(f"✅ Successfully deleted chat {deleted_count} using alternative method")
            
            # Check if we've reached the maximum number of chats to delete
            if max_chats and deleted_count >= max_chats:
                logger.info(f"Reached maximum number of chats to delete ({max_chats})")
                break
                
            # Give the page time to update
            time.sleep(3)
            
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            # Refresh the page if we encounter an error
            driver.refresh()
            time.sleep(5)
    
    return deleted_count

def try_alternative_delete(driver, chat_element):
    """Try alternative methods to delete a chat"""
    try:
        # Method 1: Try to click on the chat first to select it
        logger.info("Trying alternative delete method: Click chat first")
        chat_element.click()
        time.sleep(2)
        
        # Method 2: Try to find a menu button or gear icon after selecting the chat
        menu_buttons = driver.find_elements(By.XPATH, 
            '//div[@aria-label="Menu" or @aria-label="תפריט" or contains(@aria-label, "More") or contains(@aria-label, "עוד")]')
        
        if menu_buttons:
            logger.info("Found menu button, clicking it")
            menu_buttons[0].click()
            time.sleep(2)
            
            # Look for delete option in the menu
            delete_options = driver.find_elements(By.XPATH, 
                '//div[contains(text(), "Delete") or contains(text(), "מחק") or contains(text(), "הסר")]')
            
            if delete_options:
                logger.info("Found delete option in menu, clicking it")
                delete_options[0].click()
                time.sleep(2)
                
                # Look for confirm button
                confirm_buttons = driver.find_elements(By.XPATH, 
                    '//div[@role="button"]//div[contains(text(), "Delete") or contains(text(), "מחק") or contains(text(), "הסר") or contains(text(), "אישור")]')
                
                if confirm_buttons:
                    logger.info("Found confirmation button, clicking it")
                    confirm_buttons[0].click()
                    time.sleep(3)
                    return True
        
        # Method 3: Try using keyboard shortcut
        logger.info("Trying keyboard shortcut method")
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.common.action_chains import ActionChains
        
        # First select the chat again to ensure it's focused
        chat_element.click()
        time.sleep(1)
        
        # Try common keyboard shortcuts for delete
        actions = ActionChains(driver)
        actions.send_keys(Keys.DELETE).perform()
        time.sleep(2)
        
        # Look for confirm button that might appear
        confirm_buttons = driver.find_elements(By.XPATH, 
            '//div[@role="button"]//div[contains(text(), "Delete") or contains(text(), "מחק") or contains(text(), "הסר") or contains(text(), "אישור")]')
        
        if confirm_buttons:
            logger.info("Found confirmation button after keyboard shortcut, clicking it")
            confirm_buttons[0].click()
            time.sleep(3)
            return True
        
        # Method 4: Try direct JavaScript approach to find and click hidden menu items
        logger.info("Trying direct JavaScript approach")
        driver.execute_script("""
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
        
        time.sleep(2)
        
        # Check for confirmation dialog again
        confirm_buttons = driver.find_elements(By.XPATH, 
            '//div[@role="button"]//div[contains(text(), "Delete") or contains(text(), "מחק") or contains(text(), "הסר") or contains(text(), "אישור")]')
        
        if confirm_buttons:
            logger.info("Found confirmation button after JavaScript approach, clicking it")
            confirm_buttons[0].click()
            time.sleep(3)
            return True
        
        return False
    except Exception as e:
        logger.error(f"Error in alternative delete method: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Facebook Messenger Chat Cleaner - Direct Method')
    parser.add_argument('--max', type=int, help='Maximum number of chats to delete')
    args = parser.parse_args()
    
    logger.info("Starting Facebook Messenger Chat Cleaner - Direct Method")
    
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
