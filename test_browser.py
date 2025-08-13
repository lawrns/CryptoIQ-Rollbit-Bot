import sys
import os
from selenium.common.exceptions import WebDriverException
from browser import init_browser

# Check if venv is active (generic)
try:
    in_venv = (hasattr(sys, 'real_prefix') or (getattr(sys, 'base_prefix', sys.prefix) != sys.prefix))
except Exception:
    in_venv = False
if not in_venv:
    print("ERROR: Virtual environment not activated. Run & .\\venv\\Scripts\\Activate.ps1 in PowerShell and retry.")
    sys.exit(1)

def main():
    driver = None
    try:
        print("About to call init_browser()...")
        driver = init_browser()
        print(f'Browser launched successfully: {driver}')

        # Keep open for manual login/testing and inspection
        import time
        time.sleep(5)
        input("Press Enter after inspecting and logging in...")

    except WebDriverException as e:
        print(f"WebDriver error: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error in test: {e}")
        raise
    finally:
        # Clean up
        try:
            if driver:
                print("Closing browser...")
                driver.quit()
        except Exception as e:
            print(f"Error closing driver: {e}")

if __name__ == "__main__":
    main()


