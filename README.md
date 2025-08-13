# CryptoIQ Trading Bot (formerly Sentinel Awakens)

## WebSocket Toggle Layover

- Open the GUI and click "WebSocket Settings".
- Toggle "Enable WebSocket Signals" to allow incoming signals from the Sentinel stream.
- Status field shows: "Connected (SYMBOL)" or "Disconnected".
- You can change the symbol (default `BTCUSDT`).
- Use "Send Test Signal" in the layover to simulate a message:

```json
{"s": "BTCUSDT", "ts": 1697059200000, "pv": 100, "cv": 120, "delta": 20, "strings": 10}
```

When enabled, incoming messages with matching `s` symbol will trigger an automatic trade:
- delta > 0 -> UP
- delta <= 0 -> DOWN

## Installing Dependencies

Activate the virtual environment and install requirements:

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

`requirements.txt` includes `websocket-client`.

## Running

```powershell
python main.py
```

If you see an error about the virtual environment, activate it first:

```powershell
.\venv\Scripts\Activate.ps1
```

### macOS

**Prerequisites:**
- Python 3.8+ installed (`python3 --version`) - Python 3.11+ recommended
- Google Chrome installed
- Terminal access

**Setup and Run:**
1. From the project directory, run the setup script:
```bash
chmod +x setup_and_run.sh run_sentinel.sh
./setup_and_run.sh
```

2. Or manually:
```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

**For subsequent runs:**
```bash
./run_sentinel.sh
```

**Troubleshooting:**

If you get SSL certificate errors during setup:
```bash
export CHROME_MAJOR_VERSION=139  # Use your Chrome major version
./run_sentinel.sh
```

To check your Chrome version:
```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --version
```

To use a specific Chrome profile:
```bash
export CHROME_PROFILE_DIR="Profile 1"  # or "Default"
./run_sentinel.sh
```

If you get "No module named 'distutils'" error (Python 3.13+):
```bash
source venv/bin/activate
pip install setuptools
```

If SSL certificate issues persist, install certificates:
```bash
/Applications/Python\ 3.13/Install\ Certificates.command
```

**Compatibility Test:**
Run the compatibility test to verify everything is working:
```bash
source venv/bin/activate
python test_macos_compatibility.py
```
# CryptoIQ-Rollbit-Bot
