import time
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

def try_click(driver, xpath_list):
    for path in xpath_list:
        try:
            btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, path)))
            driver.execute_script("arguments[0].click();", btn)
            return True
        except:
            continue
    return False

def delete_chat(driver, row):
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", row)
        menu = row.find_element(By.XPATH, './/div[@role="button"]')
        driver.execute_script("arguments[0].click();", menu)

        if not try_click(driver, [
            '//span[text()="Delete Chat"]/ancestor::div[@role="menuitem"]',
            '//span[contains(text(), "Delete")]/ancestor::div[@role="menuitem"]'
        ]):
            return False

        if not try_click(driver, [
            '//div[@role="dialog"]//span[text()="Delete Chat"]/ancestor::div[@role="button"]',
            '//div[@role="dialog"]//div[contains(@class, "button") and contains(text(), "Delete")]'
        ]):
            return False

        return True
    except:
        return False

def fast_delete_all_chats():
    driver = setup_driver()
    driver.get("https://www.facebook.com/messages")
    WebDriverWait(driver, 120).until(EC.presence_of_element_located((By.XPATH, '//div[@role="row"]')))

    deleted_total = 0
    seen_ids = set()

    while True:
        rows = driver.find_elements(By.XPATH, '//div[@role="row"]')
        new_deletes = 0

        for row in rows:
            row_id = row.id
            if row_id in seen_ids:
                continue
            if delete_chat(driver, row):
                deleted_total += 1
                new_deletes += 1
                seen_ids.add(row_id)

        if new_deletes == 0:
            previous = len(rows)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            current = len(driver.find_elements(By.XPATH, '//div[@role="row"]'))
            if current == previous:
                break

    print(f"\n✅ Done! Deleted {deleted_total} chats.")
    driver.quit()

if __name__ == "__main__":
    fast_delete_all_chats()
