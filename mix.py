import time
import pyautogui
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def setup_driver():
    options = Options()
    options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    return driver

def get_center_screen_coords(driver, element):
    location = element.location
    size = element.size
    window_position = driver.get_window_position()
    window_x, window_y = window_position['x'], window_position['y']
    center_x = window_x + location['x'] + size['width'] / 2
    center_y = window_y + location['y'] + size['height'] / 2
    return center_x, center_y

def py_click(driver, element, delay=0.2):
    x, y = get_center_screen_coords(driver, element)
    pyautogui.moveTo(x, y, duration=delay)
    pyautogui.click()

def delete_chat(driver, row, index):
    try:
        print(f"\n🔹 Deleting chat #{index + 1}")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", row)
        time.sleep(1.5)

        menu_btn = row.find_element(By.XPATH, './/div[@role="button"]')
        py_click(driver, menu_btn)
        time.sleep(1.2)

        delete_btn = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//span[contains(text(), "Delete Chat")]/ancestor::div[@role="menuitem"]'))
        )
        py_click(driver, delete_btn)
        time.sleep(1.2)

        confirm_btn = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//div[@role="dialog"]//span[contains(text(), "Delete Chat")]/ancestor::div[@role="button"]'))
        )
        py_click(driver, confirm_btn)
        time.sleep(2)

        print("✅ Chat deleted.")
        return True
    except Exception as e:
        print(f"❌ Error on chat #{index + 1}: {e}")
        return False

def load_more_chats(driver, previous_count):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)
    rows = driver.find_elements(By.XPATH, '//div[@role="row"]')
    return rows if len(rows) > previous_count else None

def main():
    driver = setup_driver()
    driver.get("https://www.facebook.com/messages")
    print("🌐 Log into Messenger manually...")

    WebDriverWait(driver, 120).until(
        EC.presence_of_element_located((By.XPATH, '//div[@role="row"]'))
    )
    print("✅ Chat list loaded.")

    seen_rows = set()
    total_deleted = 0

    while True:
        rows = driver.find_elements(By.XPATH, '//div[@role="row"]')
        print(f"\n🔄 Found {len(rows)} chat rows")

        new_deletions = 0
        for i, row in enumerate(rows):
            try:
                row_id = row.get_attribute("data-testid") or str(row.id)
                if row_id in seen_rows:
                    continue
                if delete_chat(driver, row, i):
                    total_deleted += 1
                    new_deletions += 1
                    seen_rows.add(row_id)
            except:
                continue

        if new_deletions == 0:
            print("⚠️ No new deletions. Trying to scroll for more...")
            more_rows = load_more_chats(driver, len(rows))
            if not more_rows:
                print("✅ All chats appear to be deleted.")
                break
        else:
            time.sleep(1)

    print(f"\n🎉 Finished. Total chats deleted: {total_deleted}")
    input("Press Enter to close browser...")
    driver.quit()

if __name__ == "__main__":
    main()
