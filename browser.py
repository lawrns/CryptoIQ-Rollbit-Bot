import sys
import os
from pathlib import Path
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from config import ROLLBIT_URL, SELECTORS

# Check if venv is active (generic)
try:
    in_venv = (hasattr(sys, 'real_prefix') or (getattr(sys, 'base_prefix', sys.prefix) != sys.prefix))
except Exception:
    in_venv = False
if not in_venv:
    activation_hint = (
        'Run & .\\venv\\Scripts\\Activate.ps1 in PowerShell and retry.'
        if sys.platform == 'win32'
        else 'Run source venv/bin/activate in your shell and retry.'
    )
    print(f'ERROR: Virtual environment not activated. {activation_hint}')
    sys.exit(1)

def init_browser():
    """
    Initialize and prepare an undetected Chrome browser and navigate to Rollbit.
    """
    try:
        print("Starting undetected Chrome browser...")
        
        options = uc.ChromeOptions()

        # Cross-platform Chrome user data dir (optional)
        def get_default_chrome_base_dir() -> Path:
            if sys.platform == 'win32':
                return Path(os.environ.get('LOCALAPPDATA', '')) / 'Google' / 'Chrome' / 'User Data'
            if sys.platform == 'darwin':
                return Path.home() / 'Library' / 'Application Support' / 'Google' / 'Chrome'
            # Linux and others
            return Path.home() / '.config' / 'google-chrome'

        def maybe_add_user_data_dir(chrome_options: uc.ChromeOptions) -> None:
            try:
                base_dir = get_default_chrome_base_dir()
                preferred_profile = os.environ.get('CHROME_PROFILE_DIR')
                candidates = [preferred_profile] if preferred_profile else []
                # Reasonable defaults
                candidates += ['Profile 1', 'Default']
                for candidate in candidates:
                    if not candidate:
                        continue
                    path = base_dir / candidate
                    if path.exists():
                        chrome_options.add_argument(f'--user-data-dir={path}')
                        break
            except Exception:
                # Non-fatal if not found
                pass

        maybe_add_user_data_dir(options)
        options.add_argument('--no-first-run')
        options.add_argument('--disable-extensions')
        
        # Allow overriding Chrome major version if needed
        version_env = os.environ.get('CHROME_MAJOR_VERSION')
        if version_env and version_env.isdigit():
            driver = uc.Chrome(options=options, version_main=int(version_env))
        else:
            driver = uc.Chrome(options=options)
        
        print("Navigating to Rollbit...")
        driver.get(ROLLBIT_URL)
        
        print("Browser launched with undetected-chromedriver")
        print("Check if Cloudflare challenge appears...")
        
        # Wait for manual intervention if needed
        input("Press Enter after page loads completely...")
        
        print('Browser ready')
        return driver
        
    except Exception as e:
        print(f"Error: {e}")
        raise

