from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import time
import logging
import argparse
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"fb_delete_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

def delete_facebook_chats(max_chats=None):
    """Delete Facebook Messenger chats following the exact process described."""
    
    # 1.1 Launch Chrome (headful, not headless)
    logger.info("Setting up Chrome driver")
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_experimental_option("detach", True)  # Allow interactive inspection
    
    driver = webdriver.Chrome(options=options)
    
    try:
        # 1.2 Navigate to Messenger
        logger.info("Navigating to Facebook Messenger")
        driver.get("https://www.facebook.com/messages")
        
        # 2. User Interaction Wait
        input("🟢 Log in manually, then press ENTER to continue...")
        logger.info("User logged in, proceeding with deletion")
        
        # 3. DOM Stabilization Wait
        logger.info("Waiting for DOM to stabilize")
        time.sleep(5)
        
        # Create wait and actions objects
        wait = WebDriverWait(driver, 10)
        actions = ActionChains(driver)
        
        deleted_count = 0
        skipped_count = 0
        
        # Main deletion loop
        while True:
            try:
                # 4. Chat Row Detection
                logger.info("Finding chat rows")
                rows = driver.find_elements(By.XPATH, '//div[@role="row"]')
                
                if not rows:
                    logger.info("No more chat rows found")
                    break
                    
                logger.info(f"Found {len(rows)} chat rows")
                
                # 5. Loop Over Each Chat Row (just the first one in each iteration)
                row = rows[0]  # Process only the first row as the DOM refreshes after deletion
                
                # 6. Marketplace Chat Filtering
                if "Marketplace" in row.text:
                    logger.info("Skipping Marketplace chat")
                    skipped_count += 1
                    
                    # Try to find a way to remove or skip this chat
                    try:
                        # Click on the chat to select it, then press Delete key
                        row.click()
                        time.sleep(1)
                        # Continue with next iteration
                        continue
                    except Exception as e:
                        logger.warning(f"Error trying to skip Marketplace chat: {str(e)}")
                        continue
                
                # 7. Scroll Into View + Hover
                logger.info("Scrolling chat into view and hovering")
                driver.execute_script("arguments[0].scrollIntoView(true);", row)
                actions.move_to_element(row).perform()
                time.sleep(1)  # Wait for hover effects
                
                # 8. Click ⋯ Menu Button
                logger.info("Looking for and clicking menu button")
                try:
                    # First try to find by aria-label
                    menu_buttons = row.find_elements(By.XPATH, './/div[@aria-label and @role="button"]')
                    
                    if not menu_buttons:
                        # Try alternative approach - any button in the row
                        menu_buttons = row.find_elements(By.XPATH, './/div[@role="button"]')
                    
                    if menu_buttons:
                        # Use the last button which is typically the menu
                        menu_btn = menu_buttons[-1]
                        logger.info("Found menu button, clicking it")
                        actions.move_to_element(menu_btn).click().perform()
                        time.sleep(1)
                    else:
                        logger.warning("No menu button found, trying direct right-click")
                        actions.context_click(row).perform()
                        time.sleep(1)
                except Exception as e:
                    logger.warning(f"Error clicking menu button: {str(e)}, trying context click")
                    actions.context_click(row).perform()
                    time.sleep(1)
                
                # 9. Wait for "Delete Chat" Option
                logger.info("Looking for Delete Chat option")
                try:
                    # Try multiple possible selectors for the Delete Chat option
                    delete_selectors = [
                        '//span[text()="Delete Chat"]/ancestor::div[@role="menuitem"]',
                        '//span[contains(text(), "Delete")]/ancestor::div[@role="menuitem"]',
                        '//div[contains(text(), "Delete Chat")]',
                        '//div[contains(text(), "Delete")]',
                        '//span[text()="מחק צ\'אט"]/ancestor::div[@role="menuitem"]',  # Hebrew
                        '//span[contains(text(), "מחק")]/ancestor::div[@role="menuitem"]',  # Hebrew
                    ]
                    
                    delete_btn = None
                    for selector in delete_selectors:
                        try:
                            elements = driver.find_elements(By.XPATH, selector)
                            if elements:
                                delete_btn = elements[0]
                                break
                        except:
                            continue
                    
                    if delete_btn:
                        logger.info("Found Delete Chat option, clicking it")
                        delete_btn.click()
                        time.sleep(1)
                    else:
                        logger.warning("Delete Chat option not found, trying next chat")
                        # Close any open menus by clicking elsewhere
                        actions.move_by_offset(100, 100).click().perform()
                        continue
                except Exception as e:
                    logger.warning(f"Error finding Delete Chat option: {str(e)}")
                    # Close any open menus by clicking elsewhere
                    actions.move_by_offset(100, 100).click().perform()
                    continue
                
                # 10. Confirm Deletion in Modal
                logger.info("Looking for confirmation button")
                try:
                    # Try multiple possible selectors for the confirmation button
                    confirm_selectors = [
                        '//div[@role="dialog"]//span[text()="Delete Chat"]/ancestor::div[@role="button"]',
                        '//div[@role="dialog"]//span[contains(text(), "Delete")]/ancestor::div[@role="button"]',
                        '//div[@role="dialog"]//div[contains(text(), "Delete")][@role="button"]',
                        '//div[@role="dialog"]//span[text()="מחק"]/ancestor::div[@role="button"]',  # Hebrew
                    ]
                    
                    confirm_btn = None
                    for selector in confirm_selectors:
                        try:
                            elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, selector)))
                            if elements:
                                confirm_btn = elements[0]
                                break
                        except:
                            continue
                    
                    if confirm_btn:
                        logger.info("Found confirmation button, clicking it")
                        confirm_btn.click()
                        deleted_count += 1
                        logger.info(f"✅ Deleted chat {deleted_count}")
                    else:
                        logger.warning("Confirmation button not found")
                        # Try to close the dialog by pressing Escape
                        actions.send_keys("\ue00c").perform()  # Escape key
                except Exception as e:
                    logger.warning(f"Error confirming deletion: {str(e)}")
                    # Try to close the dialog by pressing Escape
                    actions.send_keys("\ue00c").perform()  # Escape key
                
                # 11. Logging and Delay
                time.sleep(3)  # Wait for deletion to complete and DOM to update
                
                # Check if we've reached the maximum number of chats to delete
                if max_chats and deleted_count >= max_chats:
                    logger.info(f"Reached maximum number of chats to delete ({max_chats})")
                    break
                    
            except StaleElementReferenceException:
                logger.warning("Stale element reference, DOM might have been updated")
                time.sleep(2)  # Wait for DOM to stabilize
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                time.sleep(2)  # Wait and try again
        
        # 12. Post Loop
        logger.info(f"🎉 Finished processing visible chats. Deleted: {deleted_count}, Skipped: {skipped_count}")
        return deleted_count
        
    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        return 0
    finally:
        # Keep browser open for inspection (detach=True)
        pass

def main():
    parser = argparse.ArgumentParser(description='Facebook Messenger Chat Cleaner')
    parser.add_argument('--max', type=int, help='Maximum number of chats to delete')
    args = parser.parse_args()
    
    logger.info("Starting Facebook Messenger Chat Cleaner")
    
    # Delete chats
    deleted = delete_facebook_chats(max_chats=args.max)
    
    logger.info(f"Script execution completed. Total chats deleted: {deleted}")

if __name__ == "__main__":
    main()
