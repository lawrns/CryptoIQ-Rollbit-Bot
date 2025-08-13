#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -d venv ]; then
  python3 -m venv venv
fi

source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Set Chrome version to avoid SSL certificate issues during driver download
if [ -z "${CHROME_MAJOR_VERSION:-}" ]; then
  export CHROME_MAJOR_VERSION=139
  echo "Using Chrome version: $CHROME_MAJOR_VERSION"
fi

python main.py


