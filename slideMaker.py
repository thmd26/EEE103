import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import img2pdf

# === CONFIG ===
HTML_FILE = r"C:\Users\Rafid\Downloads\EEE103_Web\L6.html"   # change if needed
OUT_DIR = r"C:\Users\Rafid\Downloads\EEE103_Web\slide_exports"
OUT_PDF = os.path.join(OUT_DIR, "L6.pdf")
MAX_SLIDES = 18            # safety limit: increase if you have more slides
WAIT_AFTER_ACTION = 0.5    # seconds to wait after keypress/render
CHROME_PATH = None         # set to chromedriver executable path if not in PATH
# ==============

os.makedirs(OUT_DIR, exist_ok=True)

opts = Options()
opts.add_argument("--start-maximized")
opts.add_argument("--disable-infobars")
opts.add_argument("--disable-extensions")
# optional: run headless (no GUI) — screenshots still work but rendering may differ
# opts.add_argument("--headless=new")

service = ChromeService(executable_path=CHROME_PATH) if CHROME_PATH else ChromeService()
driver = webdriver.Chrome(service=service, options=opts)

try:
    file_url = "file:///" + HTML_FILE.replace("\\", "/")
    driver.get(file_url)

    wait = WebDriverWait(driver, 15)
    # wait for slide container to appear
    slide_sel = ".bg-white.rounded-xl.shadow-2xl"
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, slide_sel)))

    body = driver.find_element(By.TAG_NAME, "body")
    saved_images = []
    previous_png = None

    for i in range(MAX_SLIDES):
        # reveal all steps on current slide by pressing 'b'
        body.send_keys("b")
        time.sleep(WAIT_AFTER_ACTION)

        # capture only slide container for consistent pages
        try:
            el = driver.find_element(By.CSS_SELECTOR, slide_sel)
        except:
            # fallback: capture entire viewport
            el = None

        img_path = os.path.join(OUT_DIR, f"slide_{i+1:03d}.png")
        if el:
            # element screenshot (PNG)
            el.screenshot(img_path)
        else:
            driver.save_screenshot(img_path)

        # if the screenshot is identical to previous one, we may have reached the end — stop.
        if previous_png and os.path.exists(previous_png):
            with open(previous_png, "rb") as f1, open(img_path, "rb") as f2:
                if f1.read() == f2.read():
                    # if two identical screenshots in a row, assume no more new slides
                    os.remove(img_path)
                    break
        previous_png = img_path
        saved_images.append(img_path)

        # advance to next slide (Tab) and wait
        body.send_keys(Keys.TAB)
        time.sleep(WAIT_AFTER_ACTION)

    if not saved_images:
        print("No slides captured.")
    else:
        # convert PNGs to single PDF (A4 landscape-like fitting)
        # img2pdf will keep image size; use default conversion
        with open(OUT_PDF, "wb") as f:
            f.write(img2pdf.convert(saved_images))
        print("PDF written to:", OUT_PDF)

finally:
    driver.quit()