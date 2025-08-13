#!/usr/bin/env python3
"""
macOS Compatibility Test for Sentinel Awakens Trading Interface
Tests all components without opening browser or GUI windows.
"""

import sys
import os
import platform
from pathlib import Path

def test_python_version():
    """Test Python version compatibility"""
    print("🐍 Testing Python version...")
    version = sys.version_info
    print(f"   Python {version.major}.{version.minor}.{version.micro}")
    if version.major >= 3 and version.minor >= 8:
        print("   ✅ Python version compatible")
        return True
    else:
        print("   ❌ Python version too old (need 3.8+)")
        return False

def test_venv():
    """Test virtual environment"""
    print("📦 Testing virtual environment...")
    try:
        in_venv = (hasattr(sys, 'real_prefix') or (getattr(sys, 'base_prefix', sys.prefix) != sys.prefix))
        if in_venv:
            print("   ✅ Virtual environment active")
            return True
        else:
            print("   ❌ Virtual environment not active")
            return False
    except Exception as e:
        print(f"   ❌ Error checking venv: {e}")
        return False

def test_platform():
    """Test platform compatibility"""
    print("💻 Testing platform...")
    system = platform.system()
    print(f"   Platform: {system}")
    if system == "Darwin":
        print("   ✅ macOS detected")
        return True
    else:
        print(f"   ⚠️  Platform is {system}, not macOS")
        return True  # Still allow other platforms

def test_chrome_availability():
    """Test Chrome availability"""
    print("🌐 Testing Chrome availability...")
    chrome_path = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    if chrome_path.exists():
        print("   ✅ Google Chrome found")
        return True
    else:
        print("   ❌ Google Chrome not found at standard location")
        return False

def test_imports():
    """Test all required imports"""
    print("📚 Testing imports...")
    
    imports_to_test = [
        ("tkinter", "GUI framework"),
        ("selenium", "Web automation"),
        ("undetected_chromedriver", "Chrome driver"),
        ("requests", "HTTP requests"),
        ("websocket", "WebSocket client"),
        ("json", "JSON handling"),
        ("threading", "Threading support"),
        ("time", "Time utilities"),
    ]
    
    all_passed = True
    for module_name, description in imports_to_test:
        try:
            __import__(module_name)
            print(f"   ✅ {module_name} ({description})")
        except ImportError as e:
            print(f"   ❌ {module_name} ({description}): {e}")
            all_passed = False
    
    return all_passed

def test_project_files():
    """Test project file structure"""
    print("📁 Testing project files...")
    
    required_files = [
        "main.py",
        "browser.py", 
        "trading_interface.py",
        "gui_interface.py",
        "config.py",
        "requirements.txt",
        "setup_and_run.sh",
        "run_sentinel.sh",
        "README.md"
    ]
    
    all_found = True
    for filename in required_files:
        if Path(filename).exists():
            print(f"   ✅ {filename}")
        else:
            print(f"   ❌ {filename} missing")
            all_found = False
    
    return all_found

def test_script_permissions():
    """Test script permissions"""
    print("🔐 Testing script permissions...")
    
    scripts = ["setup_and_run.sh", "run_sentinel.sh"]
    all_executable = True
    
    for script in scripts:
        path = Path(script)
        if path.exists():
            if os.access(path, os.X_OK):
                print(f"   ✅ {script} is executable")
            else:
                print(f"   ❌ {script} is not executable")
                all_executable = False
        else:
            print(f"   ❌ {script} not found")
            all_executable = False
    
    return all_executable

def test_config_loading():
    """Test configuration loading"""
    print("⚙️  Testing configuration...")
    try:
        from config import ROLLBIT_URL, SELECTORS
        print(f"   ✅ Config loaded - URL: {ROLLBIT_URL[:30]}...")
        print(f"   ✅ Selectors loaded: {len(SELECTORS)} items")
        return True
    except Exception as e:
        print(f"   ❌ Config loading failed: {e}")
        return False

def main():
    """Run all compatibility tests"""
    print("🤖 SENTINEL AWAKENS - macOS Compatibility Test")
    print("=" * 50)
    
    tests = [
        test_python_version,
        test_venv,
        test_platform,
        test_chrome_availability,
        test_imports,
        test_project_files,
        test_script_permissions,
        test_config_loading,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"   ❌ Test failed with exception: {e}")
            results.append(False)
        print()
    
    print("=" * 50)
    print("📊 TEST RESULTS:")
    passed = sum(results)
    total = len(results)
    print(f"   Passed: {passed}/{total}")
    
    if passed == total:
        print("   🎉 ALL TESTS PASSED! macOS compatibility confirmed.")
        print("   Ready to run: ./run_sentinel.sh")
        return 0
    else:
        print("   ⚠️  Some tests failed. Check issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
