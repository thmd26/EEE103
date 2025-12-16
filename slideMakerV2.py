import time
import os
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import img2pdf

# --- CONFIG ---
HTML_FILE = r"C:\Users\Rafid\Downloads\EEE103_Web\L8P2.html"   # <-- your HTML file
OUT_DIR = r"C:\Users\Rafid\Downloads\EEE103_Web\slide_exports"
OUT_PDF = os.path.join(OUT_DIR, "L8P2   .pdf")
MAX_SLIDES = 100
WAIT_AFTER_ACTION = 0.6
CHROMEDRIVER_PATH = None   # set if chromedriver not in PATH, e.g. r"C:\tools\chromedriver.exe"
# ----------------

os.makedirs(OUT_DIR, exist_ok=True)

opts = Options()
opts.add_argument("--disable-infobars")
opts.add_argument("--disable-extensions")
# optional: run headless (uncomment if desired)
# opts.add_argument("--headless=new")
# set window size so screenshots are consistent
opts.add_argument("--window-size=1400,1000")

service = ChromeService(executable_path=CHROMEDRIVER_PATH) if CHROMEDRIVER_PATH else ChromeService()
driver = webdriver.Chrome(service=service, options=opts)

def dispatch_key(key):
    # dispatch KeyboardEvent to window so your app's window key handlers run
    script = """
    window.dispatchEvent(new KeyboardEvent('keydown', {key: arguments[0], bubbles: true, cancelable: true}));
    window.dispatchEvent(new KeyboardEvent('keyup', {key: arguments[0], bubbles: true, cancelable: true}));
    """
    driver.execute_script(script, key)

try:
    file_url = "file:///" + HTML_FILE.replace("\\", "/")
    driver.get(file_url)

    wait = WebDriverWait(driver, 15)
    # adapt selector to your slide container classes
    slide_sel = ".bg-white.rounded-xl.shadow-2xl"  # matches L8P1.html container
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, slide_sel)))

    saved_images = []
    previous_bytes = None

    for i in range(MAX_SLIDES):
        # reveal everything on current slide by dispatching 'b'
        dispatch_key('b')
        time.sleep(WAIT_AFTER_ACTION)

        # find slide element and screenshot it
        try:
            el = driver.find_element(By.CSS_SELECTOR, slide_sel)
            img_path = os.path.join(OUT_DIR, f"slide_{i+1:03d}.png")
            el.screenshot(img_path)
        except Exception:
            # fallback to full page screenshot
            img_path = os.path.join(OUT_DIR, f"slide_{i+1:03d}.png")
            driver.save_screenshot(img_path)

        # check identical image to previous (simple end detection)
        with open(img_path, "rb") as f:
            cur_bytes = f.read()
        if previous_bytes is not None and cur_bytes == previous_bytes:
            os.remove(img_path)
            print("Detected repeated screenshot — assuming end of slides.")
            break
        previous_bytes = cur_bytes
        saved_images.append(img_path)
        print("Captured", img_path)

        # advance slide by dispatching Tab (your app also handles ArrowRight/Tab)
        dispatch_key('Tab')
        time.sleep(WAIT_AFTER_ACTION)

    if not saved_images:
        print("No slides captured. Check selector, page load or chromedriver errors.")
        sys.exit(1)

    # convert to single PDF
    with open(OUT_PDF, "wb") as fpdf:
        fpdf.write(img2pdf.convert(saved_images))
    print("PDF created at:", OUT_PDF)

finally:
    driver.quit()