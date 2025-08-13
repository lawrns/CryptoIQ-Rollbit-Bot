import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def init_undetected_browser():
    """Initialize undetected Chrome browser"""
    options = uc.ChromeOptions()
    options.add_argument(r'--user-data-dir=C:\Users\Usuario\AppData\Local\Google\Chrome\User Data\Profile 1')
    options.add_argument('--no-first-run')
    options.add_argument('--disable-extensions')
    
    # Specify Chrome version to match your installed version (138)
    driver = uc.Chrome(options=options, version_main=138)
    driver.get('https://rollbit.com/trading/BTC')
    
    print("Browser launched with undetected-chromedriver")
    print("Check if Cloudflare challenge appears...")
    
    # Wait for manual intervention if needed
    input("Press Enter after page loads completely...")
    
    return driver

if __name__ == "__main__":
    driver = init_undetected_browser()
    # Keep browser open
    input("Press Enter to close browser...")
    driver.quit()
