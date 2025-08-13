#!/usr/bin/env bash
# Double-clickable launcher for macOS
# Launches the CryptoIQ Trading Bot in this folder.

set -e
cd "$(dirname "$0")"
chmod +x run_sentinel.sh setup_and_run.sh || true

# Keep Terminal window open on exit (success or error) for diagnostics
trap 'status=$?; echo; if [ $status -ne 0 ]; then echo "[ERROR] Launcher exited with status $status"; fi; read -r -p "Press Enter to close this window..." _' EXIT

# Default Chrome version (can be overridden in the environment)
if [ -z "${CHROME_MAJOR_VERSION:-}" ]; then
  export CHROME_MAJOR_VERSION=139
fi

# Run setup on first launch
if [ ! -d venv ]; then
  echo "[Launcher] First run detected. Setting up virtual environment..."
  ./setup_and_run.sh
else
  echo "[Launcher] Using existing venv. Starting application..."
  ./run_sentinel.sh
fi

