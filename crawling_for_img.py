from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
from urllib.request import urlretrieve
from pathlib import Path
from rembg import remove, new_session
from PIL import Image

driver = webdriver.Chrome()
driver.implicitly_wait(10)
driver.get('https://www.safetykorea.kr/release/itemSearch')
time.sleep(3)

NO_BG_IMAGES_DIR = "C:/KDH/kc-finder-test/no_bg_images/"
if not os.path.isdir(NO_BG_IMAGES_DIR):
    os.makedirs(NO_BG_IMAGES_DIR)

child_link = '#goList > div > div.left > ul > li:nth-child(6)'
links_selector = 'body > div.container > div.contents_area > div > div > div.tb_wrap.pt10 > table > tbody > tr'
specific_row_selector = 'body > div.container > div.contents_area > div > div > div.tb_wrap.pt10 > table > tbody > tr:nth-child(2)'
img_selector = 'body > div.container > div.contents_area > div > div:nth-child(6) > div > table > tbody > tr > td > p > img'

#  rembg
# 'u2net' (일반 용도), 'u2netp' (경량), 'u2net_human_seg' (인물),
# 'u2net_cloth_seg' (의류), 'isnet-general-use' (일반),
# 'silueta' (경량), 'isnet-anime' (애니메이션),
# 'birefnet-general' (일반적인 물체), 'birefnet-portrait' (인물 초상)
MODEL_NAME = 'birefnet-general'

session = new_session(MODEL_NAME)

def remove_background_from_url(img_url, output_path):
    try:
        temp_file = "temp_download.jpg"
        urlretrieve(img_url, temp_file)

        input_image = Image.open(temp_file)

        output_image = remove(input_image, session=session, alpha_matting=True, alpha_matting_foreground_threshold=240,
                                    alpha_matting_background_threshold=10, alpha_matting_erode_size=10)

        output_image.save(output_path)

        if os.path.exists(temp_file):
            os.remove(temp_file)

        return True
    except Exception:
        return False

try:
    wait = WebDriverWait(driver, 10)

    first_category = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, child_link)))
    first_category.click()
    time.sleep(1)

    sub_category = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'javascript:goItemSearch(8010100)')]")))
    sub_category.click()

    max_pages = 10

    for page_index in range(max_pages):
        current_page = page_index + 1

        if page_index > 0:
            try:
                driver.execute_script(f"goPage({page_index})")
                time.sleep(2)
            except Exception:
                break

        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, links_selector)))
        all_rows = driver.find_elements(By.CSS_SELECTOR, links_selector)

        if not all_rows:
            break

        start_index = 1

        for i in range(start_index, len(all_rows)):
            try:
                all_rows = driver.find_elements(By.CSS_SELECTOR, links_selector)
                if i >= len(all_rows):
                    break

                driver.execute_script("arguments[0].scrollIntoView(true);", all_rows[i])
                time.sleep(0.5)

                all_rows[i].click()

                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, img_selector)))
                    img_element = driver.find_element(By.CSS_SELECTOR, img_selector)
                    driver.execute_script("arguments[0].scrollIntoView(true);", img_element)
                    time.sleep(0.5)

                    img_src = img_element.get_attribute('src')
                    if img_src:
                        no_bg_file_name = f"page{current_page}_item{i + 1}.png"
                        no_bg_file_path = os.path.join(NO_BG_IMAGES_DIR, no_bg_file_name)
                        remove_background_from_url(img_src, no_bg_file_path)

                except Exception:
                    screenshot_path = os.path.join(NO_BG_IMAGES_DIR, f"error_p{current_page}_item{i + 1}.png")
                    driver.save_screenshot(screenshot_path)

                driver.back()

                wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, links_selector)))
                time.sleep(1)

            except Exception:
                driver.get('https://www.safetykorea.kr/release/itemSearch')
                time.sleep(2)

                first_category = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, child_link)))
                first_category.click()
                time.sleep(1)

                sub_category = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'javascript:goItemSearch(8010100)')]")))
                sub_category.click()

                if page_index > 0:
                    try:
                        driver.execute_script(f"goPage({page_index})")
                        time.sleep(2)
                    except:
                        break

                wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, links_selector)))

except Exception:
    pass

finally:
    driver.quit()