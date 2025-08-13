import sys
import os
import time
from browser import init_browser
from trading_interface import TradingInterface
from gui_interface import TradingGUI
from selenium.webdriver.common.by import By
from config import SELECTORS, DEBUG_UI_SCAN, DEBUG_NETWORK_SPY

# Check if venv is active (generic and reliable)
try:
    in_venv = (hasattr(sys, 'real_prefix') or (getattr(sys, 'base_prefix', sys.prefix) != sys.prefix))
except Exception:
    in_venv = False
if not in_venv:
    hint = (
        "Run & .\\venv\\Scripts\\Activate.ps1 in PowerShell and retry."
        if sys.platform == 'win32'
        else "Run 'python3 -m venv venv && source venv/bin/activate' then 'pip install -r requirements.txt'"
    )
    print(f"ERROR: Virtual environment not activated. {hint}")
    sys.exit(1)

def debug_place_bet_button(driver):
    """Debug function to find the place bet button"""
    print("\n=== DEBUGGING PLACE BET BUTTON ===")
    
    # Try various selectors for place bet button
    place_bet_selectors = [
        'button:contains("PLACE BET")',
        'button:contains("BET")',
        'button[class*="css-"]',
        '[class*="place"]',
        '[class*="bet"]',
        'button[style*="background"]',
        'button[style*="green"]',
        '.css-1wit1e6',  # Current selector
        'button.css-1wit1e6',
        'div[class*="css-"] button',
    ]
    
    for selector in place_bet_selectors:
        try:
            if 'contains' in selector:
                # Use XPath for text-based selectors
                xpath_selector = f"//button[contains(text(), 'PLACE BET') or contains(text(), 'BET')]"
                elements = driver.find_elements(By.XPATH, xpath_selector)
                print(f"XPATH '{xpath_selector}': {len(elements)} elements")
            else:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                print(f"'{selector}': {len(elements)} elements")
            
            if len(elements) > 0 and len(elements) < 10:  # Show details for reasonable amounts
                for i, elem in enumerate(elements):
                    try:
                        text = elem.text.strip()
                        classes = elem.get_attribute('class')
                        tag = elem.tag_name
                        href = elem.get_attribute('href')
                        onclick = elem.get_attribute('onclick')
                        style = elem.get_attribute('style')
                        enabled = elem.is_enabled()
                        displayed = elem.is_displayed()
                        print(f"  [{i}] <{tag}> Text: '{text}' | Enabled: {enabled} | Displayed: {displayed}")
                        print(f"      Classes: '{classes}'")
                        if href:
                            print(f"      href: '{href}'")
                        if onclick:
                            print(f"      onclick: '{onclick}'")
                        print(f"      Style: '{style[:100]}...' " if len(style) > 100 else f"      Style: '{style}'")
                    except Exception as e:
                        print(f"  [{i}] Error getting details: {e}")
        except Exception as e:
            print(f"'{selector}': ERROR - {e}")
    
    print("=== END PLACE BET DEBUG ===\n")

def debug_direction_buttons(driver):
    """Debug function to find UP and DOWN buttons"""
    print("\n=== DEBUGGING UP/DOWN BUTTONS ===")
    
    # Try various selectors for direction buttons
    direction_selectors = [
        '.css-1p91j2k',  # Current UP selector
        '.css-qv9fap',   # Current DOWN selector
        'button[class*="css-1p91j2k"]',
        'button[class*="css-qv9fap"]',
        'button:contains("UP")',
        'button:contains("DOWN")',
        'button:contains("BUY")',
        'button:contains("SELL")',
        '[class*="up"]',
        '[class*="down"]',
        '[class*="buy"]',
        '[class*="sell"]',
        'button[style*="green"]',
        'button[style*="red"]',
    ]
    
    for selector in direction_selectors:
        try:
            if 'contains' in selector:
                # Use XPath for text-based selectors
                if 'UP' in selector or 'BUY' in selector:
                    xpath_selector = f"//button[contains(text(), 'UP') or contains(text(), 'BUY')]"
                else:
                    xpath_selector = f"//button[contains(text(), 'DOWN') or contains(text(), 'SELL')]"
                elements = driver.find_elements(By.XPATH, xpath_selector)
                print(f"XPATH '{xpath_selector}': {len(elements)} elements")
            else:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                print(f"'{selector}': {len(elements)} elements")
            
            if len(elements) > 0 and len(elements) < 5:  # Show details for reasonable amounts
                for i, elem in enumerate(elements):
                    try:
                        text = elem.text.strip()
                        classes = elem.get_attribute('class')
                        tag = elem.tag_name
                        href = elem.get_attribute('href')
                        onclick = elem.get_attribute('onclick')
                        style = elem.get_attribute('style')
                        enabled = elem.is_enabled()
                        displayed = elem.is_displayed()
                        print(f"  [{i}] <{tag}> Text: '{text}' | Enabled: {enabled} | Displayed: {displayed}")
                        print(f"      Classes: '{classes}'")
                        if href:
                            print(f"      href: '{href}'")
                        if onclick:
                            print(f"      onclick: '{onclick}'")
                        if 'background' in style.lower() or 'color' in style.lower():
                            print(f"      Style: '{style[:150]}...' " if len(style) > 150 else f"      Style: '{style}'")
                    except Exception as e:
                        print(f"  [{i}] Error getting details: {e}")
        except Exception as e:
            print(f"'{selector}': ERROR - {e}")
    
    print("=== END UP/DOWN DEBUG ===\n")

def test_direction_clicks(driver):
    """Test clicking UP and DOWN buttons to see what happens"""
    print("\n=== TESTING DIRECTION CLICKS ===")
    
    try:
        # Test UP button
        print("Testing UP button click...")
        up_button = driver.find_element(By.CSS_SELECTOR, '.css-1p91j2k')
        up_button.click()
        time.sleep(1)
        
        # Check if any popups opened
        popups = driver.find_elements(By.CSS_SELECTOR, '[class*="modal"], [class*="popup"], [class*="dialog"]')
        print(f"After UP click: {len(popups)} popups detected")
        
        # Close any popups
        close_buttons = driver.find_elements(By.CSS_SELECTOR, '[class*="close"], [aria-label="close"], button[class*="close"]')
        for btn in close_buttons:
            if btn.is_displayed():
                btn.click()
                print("Closed popup")
        
        time.sleep(1)
        
        # Test DOWN button
        print("Testing DOWN button click...")
        down_button = driver.find_element(By.CSS_SELECTOR, '.css-qv9fap')
        down_button.click()
        time.sleep(1)
        
        # Check if any popups opened
        popups = driver.find_elements(By.CSS_SELECTOR, '[class*="modal"], [class*="popup"], [class*="dialog"]')
        print(f"After DOWN click: {len(popups)} popups detected")
        
        # Close any popups
        close_buttons = driver.find_elements(By.CSS_SELECTOR, '[class*="close"], [aria-label="close"], button[class*="close"]')
        for btn in close_buttons:
            if btn.is_displayed():
                btn.click()
                print("Closed popup")
        
    except Exception as e:
        print(f"Error testing clicks: {e}")
    
    print("=== END DIRECTION CLICK TEST ===\n")

def find_real_trading_buttons(driver):
    """Find the actual clickable trading buttons"""
    print("\n=== FINDING REAL TRADING BUTTONS ===")
    
    # Get all buttons and show their details
    try:
        buttons = driver.find_elements(By.CSS_SELECTOR, 'button, a')
        print(f"Found {len(buttons)} total buttons")
        
        for i, btn in enumerate(buttons):
            try:
                text = btn.text.strip()
                classes = btn.get_attribute('class')
                tag = btn.tag_name
                href = btn.get_attribute('href')
                enabled = btn.is_enabled()
                displayed = btn.is_displayed()
                
                # Show all buttons that are enabled and displayed
                if enabled and displayed:
                    print(f"  [{i}] <{tag}> Text: '{text}' | Classes: '{classes}'")
                    if href:
                        print(f"      href: '{href}'")
                    
            except Exception as e:
                print(f"  [{i}] Error getting details: {e}")
                
    except Exception as e:
        print(f"Error finding buttons: {e}")
    
    print("=== END REAL TRADING BUTTONS ===\n")

def find_trading_interface_elements(driver):
    """Find all trading interface elements"""
    print("\n=== FINDING TRADING INTERFACE ELEMENTS ===")
    
    # Look for elements with trading-related classes
    trading_selectors = [
        '[class*="up"]',
        '[class*="down"]', 
        '[class*="buy"]',
        '[class*="sell"]',
        '[class*="long"]',
        '[class*="short"]',
        '[class*="trade"]',
        '[class*="bet"]',
        '[class*="place"]',
        '[class*="position"]'
    ]
    
    for selector in trading_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                print(f"'{selector}': {len(elements)} elements")
                for i, elem in enumerate(elements[:5]):  # Show first 5
                    try:
                        text = elem.text.strip()
                        classes = elem.get_attribute('class')
                        tag = elem.tag_name
                        href = elem.get_attribute('href')
                        clickable = elem.is_enabled() and elem.is_displayed()
                        
                        print(f"  [{i}] <{tag}> Text: '{text}' | Clickable: {clickable}")
                        print(f"      Classes: '{classes}'")
                        if href:
                            print(f"      href: '{href}'")
                    except Exception as e:
                        print(f"  [{i}] Error: {e}")
        except Exception as e:
            print(f"'{selector}': ERROR - {e}")
    
    print("=== END TRADING INTERFACE ELEMENTS ===\n")

def main():
    driver = None
    try:
        print("Starting browser...")
        driver = init_browser()
        print("Browser initialized successfully!")
        
        # Check if logged in
        try:
            login_button = driver.find_element(By.XPATH, "//button[contains(text(), 'LOGIN')]")
            print("Not logged in - please login manually")
            input("Press Enter after logging in...")
        except:
            print("Appears to be logged in!")
        
        # Run debug scans before initializing TradingInterface (gated by flags)
        if DEBUG_UI_SCAN:
            find_real_trading_buttons(driver)
            find_trading_interface_elements(driver)
            debug_direction_buttons(driver)
            debug_place_bet_button(driver)

        # Initialize trading interface
        trading = TradingInterface(driver)
        # Install network spy and inspect in-panel controls once at startup
        try:
            if DEBUG_NETWORK_SPY:
                trading.start_network_spy()
            if DEBUG_UI_SCAN:
                trading.inspect_in_panel_controls()
        except Exception:
            pass
        
        # Launch GUI
        print("Launching Sentinel Awakens Trading Interface...")
        gui = TradingGUI(trading)
        gui.run()  # This will show the GUI window
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            print("Closing browser...")
            driver.quit()

if __name__ == "__main__":
    main()






